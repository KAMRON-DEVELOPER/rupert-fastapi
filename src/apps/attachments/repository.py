from hashlib import sha256
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models.attachment import AttachmentModel
from src.apps.shared.schemas.enums import AttachmentStatus
from src.core.boto3 import put_object_to_boto3

MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024


class AttachmentRepository:
    @classmethod
    async def create_upload(
        cls,
        session: AsyncSession,
        owner_id: UUID,
        *,
        file: UploadFile,
    ) -> AttachmentModel:
        data = await file.read()

        size_bytes = len(data)
        if size_bytes == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        if size_bytes > MAX_ATTACHMENT_BYTES:
            raise HTTPException(status_code=413, detail="File too large")

        detected_content_type = detect_content_type(data, file.filename)
        kind = infer_attachment_kind(detected_content_type)
        meta = extract_attachment_meta(data, detected_content_type, kind)
        checksum = sha256(data).hexdigest()

        record = AttachmentModel(
            owner_id=owner_id,
            object_key="",
            original_filename=file.filename,
            kind=kind,
            status=AttachmentStatus.pending,
            content_type=detected_content_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum,
            meta=meta,
        )

        session.add(record)
        await session.flush()

        object_key = f"users/{owner_id}/attachments/{record.id}/"
        record.object_key = object_key

        try:
            await put_object_to_boto3(
                object_name=object_key,
                data=data,
                content_type=detected_content_type,
            )
            record.status = AttachmentStatus.ready
            await session.flush()
            return record
        except Exception:
            record.status = AttachmentStatus.failed
            await session.flush()
            raise
