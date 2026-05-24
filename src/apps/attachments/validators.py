import json
import subprocess
from dataclasses import dataclass
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from magika import Magika
from PIL import Image

from src.core.logger import logger

"""
Magika is a novel AI-powered file type detection tool that relies on the recent
advance of deep learning to provide accurate detection. Under the hood, Magika
employs a custom, highly optimized model that only weighs about a few MBs, and
enables precise file identification within milliseconds, even when running on
a single CPU. Magika has been trained and evaluated on a dataset of ~100M samples
across 200+ content types (covering both binary and textual file formats), and it
achieves an average ~99% accuracy on our test set.
"""

m = Magika()

res = m.identify_bytes(b"function log(msg) {console.log(msg);}")
print(res.output.label)
# javascript

res = m.identify_path("./tests_data/basic/ini/doc.ini")
print(res.output.label)
# ini

with open("./tests_data/basic/ini/doc.ini", "rb") as f:
    res = m.identify_stream(f)
print(res.output.label)
# ini

# Magika ContentTypeLabel values
POSITIONABLE_IMAGE_LABELS = {"jpeg", "png", "gif", "webp"}
POSITIONABLE_VIDEO_LABELS = {"mp4"}
POSITIONABLE_VIDEO_CODECS = {"h264"}

MAX_IMAGE_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


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
    bitrate_kbps: int


@dataclass
class UploadedAttachmentData:
    key: str
    original_filename: str
    size_bytes: int
    magika_label: str
    magika_group: str
    mime_type: str
    is_displayable: bool
    media_metadata: ImageMetadata | VideoMetadata | None


async def process_upload_file(
    client,
    file: UploadFile,
    bucket: str,
    s3_key_prefix: str,
) -> UploadedAttachmentData:
    pass


def get_file_extension(file: UploadFile):
    if file.filename and "." in file.filename:
        return file.filename.rsplit(sep=".", maxsplit=1)[-1].lower()
    return None


def get_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    try:
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
        return width, height
    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get image dimensions",
        )


async def get_video_duration_using_ffprobe(file_path: str) -> float:
    result = subprocess.run(
        args=[
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            file_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = json.loads(result.stdout)
    return float(output["format"]["duration"])
