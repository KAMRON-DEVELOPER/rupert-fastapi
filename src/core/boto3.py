import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aioboto3
from aiobotocore.config import AioConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from types_aiobotocore_s3.client import S3Client
from types_aiobotocore_s3.type_defs import BucketLifecycleConfigurationTypeDef

from src.core.logger import logger
from src.core.settings import get_settings

settings = get_settings()

session = aioboto3.Session()


@asynccontextmanager
async def s3_client() -> AsyncIterator[S3Client]:
    async with session.client(
        service_name="s3",
        endpoint_url=f"{'http' if settings.debug else 'https'}://{settings.s3.endpoint}",
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_key,
        config=AioConfig(signature_version="s3v4"),
        region_name=settings.s3.region,
        verify=not settings.debug,
    ) as client:
        yield client


async def initialize_boto3():
    bucket = settings.s3.bucket_name
    async with s3_client() as s3:
        # Bucket Creation Check
        try:
            await s3.head_bucket(Bucket=bucket)
            logger.info(f"Bucket '{bucket}' already exists.")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                logger.info(f"Bucket '{bucket}' not found. Creating...")
                await s3.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={
                        "LocationConstraint": settings.s3.region
                    },
                )
                logger.info(f"Bucket '{bucket}' created.")
            else:
                logger.error(f"Error checking for bucket: {e}")
                raise

        # Policy Configuration Check
        try:
            current_policy_str = await s3.get_bucket_policy(Bucket=bucket)
            current_policy = json.loads(current_policy_str["Policy"])

            if current_policy == desired_policy:
                logger.info("✅ Bucket policy is already correct.")
            else:
                logger.warning("⚠️ Bucket policy mismatch. Updating...")
                await s3.put_bucket_policy(
                    Bucket=bucket, Policy=json.dumps(desired_policy)
                )
                logger.info("✅ Bucket policy updated.")

        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchBucketPolicy":
                logger.warning("⚠️ No bucket policy found. Setting it now.")
                await s3.put_bucket_policy(
                    Bucket=bucket, Policy=json.dumps(desired_policy)
                )
                logger.info("✅ Bucket policy has been set.")
            else:
                logger.error(f"Unhandled S3Error while getting policy: {e}")
                raise

        # Lifecycle Rule Configuration Check
        try:
            current_lifecycle = await s3.get_bucket_lifecycle_configuration(
                Bucket=bucket
            )

            if current_lifecycle.get("Rules") == desired_lifecycle["Rules"]:
                logger.info(
                    "✅ Bucket lifecycle configuration is already correct."
                )
            else:
                logger.warning(
                    "⚠️ Bucket lifecycle configuration mismatch. Updating..."
                )
                await s3.put_bucket_lifecycle_configuration(
                    Bucket=bucket, LifecycleConfiguration=desired_lifecycle
                )
                logger.info("✅ Bucket lifecycle configuration updated.")

        except ClientError as e:
            if (
                e.response.get("Error", {}).get("Code")
                == "NoSuchLifecycleConfiguration"
            ):
                logger.warning(
                    "⚠️ No lifecycle configuration found. Setting it now."
                )
                await s3.put_bucket_lifecycle_configuration(
                    Bucket=bucket, LifecycleConfiguration=desired_lifecycle
                )
                logger.info("✅ Bucket lifecycle configuration has been set.")
            else:
                logger.error(
                    f"Unhandled S3Error while getting lifecycle config: {e}"
                )
                raise


async def get_object_from_boto3(object_name: str) -> bytes:
    async with s3_client() as s3:
        try:
            response = await s3.get_object(
                Bucket=settings.s3.bucket_name, Key=object_name
            )
            return await response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to get object '{object_name}': {e}")
            raise ValueError(f"Could not retrieve object: {e}")


async def put_object_to_boto3(
    object_name: str,
    data: bytes,
    content_type: str,
    old_object_name: str | None = None,
    for_update: bool = False,
):
    async with s3_client() as s3:
        try:
            if for_update and old_object_name:
                await s3.delete_object(
                    Bucket=settings.s3.bucket_name, Key=old_object_name
                )

            await s3.put_object(
                Bucket=settings.s3.bucket_name,
                Key=object_name,
                Body=data,
                ContentType=content_type,
                ContentLength=len(data),
            )
        except ClientError as e:
            logger.error(f"Failed to put object '{object_name}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not upload object",
            )


async def put_file_to_boto3(
    object_name: str,
    file_path: Path,
    content_type: str,
    old_object_name: str | None = None,
    for_update=False,
) -> str:
    async with s3_client() as s3:
        try:
            if for_update and old_object_name:
                await s3.delete_object(
                    Bucket=settings.s3.bucket_name, Key=old_object_name
                )

            logger.debug(f"Uploading file: {file_path} as {object_name}")

            await s3.upload_file(
                Filename=str(file_path),
                Bucket=settings.s3.bucket_name,
                Key=object_name,
                ExtraArgs={"ContentType": content_type},
            )
            return object_name
        except ClientError as e:
            logger.error(f"Failed to upload file '{file_path}': {e}")
            raise ValueError(f"Could not upload file: {e}")
        except FileNotFoundError:
            logger.error(f"File not found for upload: {file_path}")
            raise


async def delete_objects_from_boto3(keys: list[str]) -> None:
    async with s3_client() as s3:
        try:
            # AWS S3 strictly limits delete_objects to 1000 items per request.
            # We batch them to prevent MalformedXML crashes on large deletions.
            for i in range(0, len(keys), 1000):
                batch = keys[i : i + 1000]
                await s3.delete_objects(
                    Bucket=settings.s3.bucket_name,
                    Delete={"Objects": [{"Key": key} for key in batch]},
                )
        except ClientError as e:
            logger.error(f"Failed to delete objects: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete object(s)",
            )


async def wipe_objects_from_boto3(user_id: str) -> None:
    async with s3_client() as s3:
        try:
            paginator = s3.get_paginator("list_objects_v2")
            object_keys_to_delete = []
            async for page in paginator.paginate(
                Bucket=settings.s3.bucket_name, Prefix=f"users/{user_id}/"
            ):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj.get("Key")
                        if key:
                            object_keys_to_delete.append(key)

            if object_keys_to_delete:
                await delete_objects_from_boto3(object_keys_to_delete)
            else:
                logger.info(f"No objects found to wipe for user '{user_id}'.")

        except ClientError as e:
            logger.error(f"Failed to wipe objects for user '{user_id}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not wipe user objects",
            )


async def remove_pending_tags_from_s3(keys: list[str]) -> None:
    """
    Strips tags from the specified objects so the S3 lifecycle rule ignores them.
    Call this when the domain logic claims the uploaded attachments.
    """
    async with s3_client() as s3:

        async def _remove_tag(key: str):
            try:
                await s3.put_object_tagging(
                    Bucket=settings.s3.bucket_name,
                    Key=key,
                    Tagging={"TagSet": []},
                )
            except ClientError as e:
                logger.error(f"Failed to remove tags for {key}: {e}")

        await asyncio.gather(*(_remove_tag(key) for key in keys))


desired_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            "Resource": f"arn:aws:s3:::{settings.s3.bucket_name}/*",
        }
    ],
}

desired_lifecycle: BucketLifecycleConfigurationTypeDef = {
    "Rules": [
        {
            "ID": "DeleteOrphanPendingAttachments",
            "Filter": {"Tag": {"Key": "is_pending", "Value": "true"}},
            "Status": "Enabled",
            "Expiration": {"Days": 1},
        }
    ]
}
