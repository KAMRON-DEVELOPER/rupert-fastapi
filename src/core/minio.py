import json
from io import BytesIO
from pathlib import Path

import aiohttp
from miniopy_async.api import Minio
from miniopy_async.datatypes import Object
from miniopy_async.error import MinioException, S3Error
from miniopy_async.helpers import ObjectWriteResult

from src.core.logger import logger
from src.core.settings import get_settings

settings = get_settings()

minio_client: Minio = Minio(
    access_key=settings.s3.access_key_id,
    secret_key=settings.s3.secret_key,
    endpoint=settings.s3.endpoint,
    region=None if settings.debug else settings.s3.region,
    secure=False if settings.debug else True,
    cert_check=False if settings.debug else True,
)


async def initialize_minio():
    try:
        # Ensure bucket exists
        if not await minio_client.bucket_exists(settings.s3.bucket_name):
            logger.info(f"Bucket {settings.s3.bucket_name} not found. Creating...")
            await minio_client.make_bucket(settings.s3.bucket_name)
            logger.info(f"Bucket {settings.s3.bucket_name} created.")
        else:
            logger.info(f"Bucket {settings.s3.bucket_name} exists.")

        # Check and apply policy
        try:
            if settings.debug:
                return
            current_policy_str = await minio_client.get_bucket_policy(settings.s3.bucket_name)
            if current_policy_str:
                current_policy = json.loads(current_policy_str)
                if current_policy == desired_policy:
                    logger.info("✅ Bucket policy is already correct.")
                else:
                    logger.warning("⚠️ Bucket policy mismatch. Updating...")
                    await minio_client.set_bucket_policy(settings.s3.bucket_name, json.dumps(desired_policy))
                    logger.info("✅ Bucket policy updated.")
            else:
                logger.warning("⚠️ Bucket policy response empty. Applying desired policy...")
                await minio_client.set_bucket_policy(settings.s3.bucket_name, json.dumps(desired_policy))

        except S3Error as s3e:
            if s3e.code == "NoSuchBucketPolicy":
                logger.warning("⚠️ No bucket policy found. Setting it...")
                await minio_client.set_bucket_policy(settings.s3.bucket_name, json.dumps(desired_policy))
                logger.info("✅ Policy applied due to NoSuchBucketPolicy.")
            else:
                logger.error(f"Unhandled S3Error while getting policy: {s3e}")
                raise s3e

    except MinioException as me:
        print(f"🌋 MinioException in initialize_minio, e: {me}, type: {type(me)}")
    except Exception as e:
        print(f"🌋 Exception in initialize_minio, e: {e}, type: {type(e)}")


async def get_object_from_minio(object_name: str) -> bytes:
    try:
        async with aiohttp.ClientSession():
            return await (
                await minio_client.get_object(bucket_name=settings.s3.bucket_name, object_name=object_name)
            ).read()
    except Exception as e:
        print(f"Exception in get_data_from_minio: {e}")
        raise ValueError("Exception in get_data_from_minio: {e}")


async def put_object_to_minio(
    object_name: str, data: bytes, content_type: str, old_object_name: str | None = None, for_update: bool = False
) -> str:
    try:
        if for_update and old_object_name:
            await minio_client.remove_object(bucket_name=settings.s3.bucket_name, object_name=old_object_name)

        _data = BytesIO(data)  # noqa
        result: ObjectWriteResult = await minio_client.put_object(
            bucket_name=settings.s3.bucket_name,
            object_name=object_name,
            data=_data,
            length=len(data),
            content_type=content_type,
        )

        return result.object_name
    except Exception as e:
        logger.warning(f"Exception in put_data_to_minio: {e}")
        raise ValueError(f"Exception in put_data_to_minio: {e}")


async def put_file_to_minio(
    object_name: str, file_path: Path, content_type: str, old_object_name: str | None = None, for_update=False
) -> str:
    try:
        if for_update and old_object_name:
            await minio_client.remove_object(bucket_name=settings.s3.bucket_name, object_name=old_object_name)

        logger.debug(f"file_path: {file_path}, content_type: {content_type}")

        result: ObjectWriteResult = await minio_client.fput_object(
            bucket_name=settings.s3.bucket_name,
            object_name=object_name,
            file_path=str(file_path),
            content_type=content_type,
        )

        return result.object_name
    except Exception as e:
        print(f"Exception in put_file_to_minio: {e}")
        raise ValueError(f"Exception in put_file_to_minio: {e}")


async def remove_objects_from_minio(object_names: list[str]) -> None:
    try:
        logger.debug(f"remove_objects_from_minio; object_names: {object_names}")
        for object_name in object_names:
            await minio_client.remove_object(bucket_name=settings.s3.bucket_name, object_name=object_name)
    except Exception as e:
        print(f"Exception in remove_object_from_minio: {e}")


async def wipe_objects_from_minio(user_id: str) -> None:
    try:
        list_objects: list[Object] = await minio_client.list_objects(
            bucket_name=settings.s3.bucket_name, prefix=f"users/{user_id}/", recursive=True
        )
        for user_object in list_objects:
            await remove_objects_from_minio(object_names=[f"{user_object.object_name}"])
    except Exception as e:
        print(f"Exception in wipe_objects_from_minio: {e}")
        raise ValueError(f"Exception in wipe_objects_from_minio: {e}")


desired_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            # "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
            "Resource": f"arn:aws:s3:::{settings.s3.bucket_name}/*",
        }
    ],
}
