import asyncio
from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, File, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from types_aiobotocore_s3.client import S3Client

from src.apps.attachments.validators import (
    UploadAttachmentData,
    process_upload_file,
)
from src.apps.shared.models.attachment import AttachmentModel
from src.apps.shared.schemas import MessageResponse
from src.apps.shared.schemas.attachment import (
    AttachmentWithPositionableResponse,
    UploadAttachmentsResponse,
)
from src.apps.shared.schemas.enums import AttachmentStatus
from src.core.boto3 import delete_objects_from_boto3, s3_client
from src.core.database import sessionDep
from src.core.logger import logger
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import authDep

settings = get_settings()
upload_router = APIRouter()


@upload_router.post("/", response_model=UploadAttachmentsResponse)
async def upload_attachments(
    session: sessionDep,
    auth: authDep,
    files: Annotated[list[UploadFile], File()],
):
    user_id, _, _ = auth
    failed: list[str] = []

    sem = asyncio.Semaphore(4)
    process_results = await asyncio.gather(
        *[_process_with_sem(sem, file) for file in files],
        return_exceptions=True,
    )

    bucket: list[tuple[UploadFile, UploadAttachmentData, AttachmentModel]] = []

    for file, result in zip(files, process_results, strict=True):
        if isinstance(result, Exception):
            if (
                isinstance(result, HTTPException)
                and result.status_code
                == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            ):
                raise result

            failed.append(_filename(file))
            logger.error(
                f"Failed to process attachment '{_filename(file)}': {result}"
            )
            continue

        assert isinstance(result, UploadAttachmentData)
        record = AttachmentModel(
            owner_id=user_id,
            object_key="",
            original_filename=result.original_filename,
            status=AttachmentStatus.pending,
            mime_type=result.mime_type,
            label=result.label,
            group=result.group,
            size_bytes=result.size_bytes,
            meta=asdict(result.meta) if result.meta else {},
        )
        bucket.append((file, result, record))

    if not bucket:
        return UploadAttachmentsResponse(attachments=[], failed=failed)

    session.add_all([record for _, _, record in bucket])
    await session.flush()

    for _, _, record in bucket:
        record.object_key = f"users/{user_id}/attachments/{record.id}"

    async with s3_client() as client:
        upload_results = await asyncio.gather(
            *[
                _upload_with_sem(
                    sem, client, file, record.object_key, record.mime_type
                )
                for file, _, record in bucket
            ],
            return_exceptions=True,
        )

    attachments = []

    for (file, data, record), result in zip(
        bucket, upload_results, strict=True
    ):
        if isinstance(result, Exception):
            await session.delete(record)
            failed.append(_filename(file))
            logger.error(
                f"Failed to upload attachment '{_filename(file)}' to S3: {result}"
            )
            continue

        attachments.append(
            AttachmentWithPositionableResponse(
                id=record.id,
                object_key=record.object_key,
                original_filename=record.original_filename,
                mime_type=record.mime_type,
                label=record.label,
                group=record.group,
                status=record.status,
                size_bytes=record.size_bytes,
                meta=record.meta,
                is_positionable=data.is_positionable,
            )
        )

    await session.commit()

    return UploadAttachmentsResponse(attachments=attachments, failed=failed)


@upload_router.delete("/")
async def delete_attachments(
    session: sessionDep,
    auth: authDep,
    ids: Annotated[
        list[UUID], Body(..., description="List of attachment IDs to delete")
    ],
):
    user_id, _, _ = auth

    stmt = select(AttachmentModel).where(
        AttachmentModel.id.in_(ids),
        AttachmentModel.owner_id == user_id,
        AttachmentModel.status == AttachmentStatus.pending,
    )

    records_to_delete = (await session.scalars(stmt)).all()

    if not records_to_delete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid pending attachments found to delete.",
        )

    object_keys = [record.object_key for record in records_to_delete]
    valid_ids = [record.id for record in records_to_delete]

    try:
        await delete_objects_from_boto3(object_keys)
    except HTTPException as e:
        logger.error(f"Failed to delete objects from S3: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not completely clear attachments from storage.",
        )

    await session.execute(
        delete(AttachmentModel).where(AttachmentModel.id.in_(valid_ids))
    )
    await session.commit()

    return MessageResponse(
        message=f"Successfully deleted {len(valid_ids)} attachments"
    )


async def _process_with_sem(sem: asyncio.Semaphore, file: UploadFile):
    async with sem:
        return await process_upload_file(file)


async def _upload_with_sem(
    sem: asyncio.Semaphore,
    client: S3Client,
    file: UploadFile,
    key: str,
    mime_type: str,
) -> None:
    async with sem:
        await file.seek(0)
        await client.put_object(
            Bucket=settings.s3.bucket_name,
            Key=key,
            Body=file.file,
            ContentType=mime_type,
            Tagging="is_pending=true",
        )


def _filename(file: UploadFile) -> str:
    return file.filename or "unknown"
