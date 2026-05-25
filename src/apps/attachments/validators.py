import asyncio
import json
import os
from dataclasses import dataclass
from io import BytesIO
from typing import cast

import aiofiles.os
import aiofiles.tempfile
from fastapi import HTTPException, UploadFile, status
from magika import Magika
from PIL import Image

from src.core.logger import logger

POSITIONABLE_IMAGE_LABELS = {"jpeg", "png", "gif", "webp"}
POSITIONABLE_VIDEO_LABELS = {"mp4"}
POSITIONABLE_VIDEO_CODECS = {"h264"}

MAX_IMAGE_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

CHUNK_SIZE = 256 * 1024
HEADER_SIZE = 65 * 1024

_magika = Magika()


@dataclass
class ImageMetadata:
    width: int
    height: int


@dataclass
class VideoMetadata:
    width: int
    height: int
    duration_seconds: float
    codec: str
    size_bytes: int
    bitrate_kbps: int


@dataclass
class UploadAttachmentData:
    original_filename: str | None
    mime_type: str
    label: str
    group: str
    size_bytes: int
    meta: ImageMetadata | VideoMetadata | None
    is_positionable: bool


async def process_upload_file(file: UploadFile) -> UploadAttachmentData:
    size_bytes = await _get_upload_file_size(file)
    if size_bytes == 0:
        raise ValueError("Empty file")

    await file.seek(0)
    header = await file.read(HEADER_SIZE)
    await file.seek(0)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _magika.identify_bytes, header)

    mime_type = result.output.mime_type
    label = result.output.label
    group = result.output.group
    meta: ImageMetadata | VideoMetadata | None = None

    _raise_if_too_large(group, size_bytes)

    if group == "video":
        tmp_path: str | None = None

        try:
            async with aiofiles.tempfile.NamedTemporaryFile(
                "wb", delete=False
            ) as tmp_file:
                tmp_path = cast(str, tmp_file.name)
                await file.seek(0)
                while chunk := await file.read(CHUNK_SIZE):
                    await tmp_file.write(chunk)
                await tmp_file.flush()

            meta = await _get_video_metadata(tmp_path)
        except Exception as e:
            logger.error(f"Failed to process video metadata: {e}")
            raise
        finally:
            if tmp_path:
                try:
                    await aiofiles.os.remove(tmp_path)
                except FileNotFoundError:
                    pass
    elif group == "image":
        try:
            meta = await loop.run_in_executor(None, _get_image_metadata, header)
        except Exception as e:
            logger.error(f"Failed to get image metadata: {e}")
            raise

    await file.seek(0)

    is_positionable = _is_positionable(label, group, meta)

    return UploadAttachmentData(
        original_filename=file.filename,
        mime_type=mime_type,
        label=label,
        group=group,
        size_bytes=size_bytes,
        meta=meta,
        is_positionable=is_positionable,
    )


async def _get_video_metadata(file_path: str) -> VideoMetadata:
    process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=10.0
        )
    except TimeoutError:
        process.kill()
        await process.communicate()
        raise

    if process.returncode != 0:
        detail = stderr.decode().strip()
        raise RuntimeError(detail or "ffprobe failed")

    data: dict = json.loads(stdout)
    streams: list[dict] = data.get("streams") or []
    format_data: dict = data.get("format") or {}

    stream: dict | None = next(
        (
            stream_data
            for stream_data in streams
            if stream_data.get("codec_type") == "video"
        ),
        None,
    )
    if not stream:
        raise ValueError("video stream not found")

    duration = format_data.get("duration") or stream.get("duration") or 0.0
    bit_rate = format_data.get("bit_rate") or stream.get("bit_rate") or 0
    size_bytes = format_data.get("size") or stream.get("size") or 0

    return VideoMetadata(
        width=int(stream["width"]),
        height=int(stream["height"]),
        duration_seconds=float(duration),
        codec=stream["codec_name"],
        size_bytes=int(size_bytes),
        bitrate_kbps=int(int(bit_rate) / 1000) if bit_rate else 0,
    )


async def _get_upload_file_size(file: UploadFile) -> int:
    size = file.size
    if size is not None:
        return size

    loop = asyncio.get_running_loop()

    def _read_size() -> int:
        pos = file.file.tell()
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(pos, os.SEEK_SET)
        return size

    return await loop.run_in_executor(None, _read_size)


def _raise_if_too_large(group: str, size_bytes: int) -> None:
    max_size = (
        MAX_IMAGE_SIZE
        if group == "image"
        else (MAX_VIDEO_SIZE if group == "video" else MAX_FILE_SIZE)
    )
    if size_bytes > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size for {group}",
        )


def _get_image_metadata(header: bytes) -> ImageMetadata:
    with Image.open(BytesIO(header)) as image:
        return ImageMetadata(image.width, image.height)


def _is_positionable(
    label: str, group: str, meta: ImageMetadata | VideoMetadata | None
) -> bool:
    if group == "image":
        return label in POSITIONABLE_IMAGE_LABELS
    if group == "video" and isinstance(meta, VideoMetadata):
        return (
            label in POSITIONABLE_VIDEO_LABELS
            and meta.codec in POSITIONABLE_VIDEO_CODECS
        )
    return False
