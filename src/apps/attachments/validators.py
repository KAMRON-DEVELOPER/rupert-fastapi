from datetime import timedelta
from io import BytesIO
import json
import subprocess
from fastapi import HTTPException, UploadFile, status
from magika import Magika
from src.apps.shared.schemas.enums import AttachmentKind
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


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/apng",
    "image/gif",
    "image/svg",
    "image/webp",
    "image/avif",
    "image/bmp",
    "image/heic",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/x-matroska",
    "video/quicktime",
    "video/x-msvideo",
}
ALLOWED_AUDIO_TYPES = {
    "audio/aac",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
}
ALLOWED_DOC_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
ALL_ALLOWED_TYPES = (
    ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_DOC_TYPES
)

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200 MB
MAX_DOC_SIZE = 50 * 1024 * 1024  # 50 MB

ORPHAN_TTL = timedelta(hours=24)


def _kind_for_mime(mime: str) -> AttachmentKind:
    if mime in ALLOWED_IMAGE_TYPES:
        return AttachmentKind.image
    if mime in ALLOWED_VIDEO_TYPES:
        return AttachmentKind.video
    return AttachmentKind.document


def _size_limit(kind: AttachmentKind) -> int:
    return {
        AttachmentKind.image: MAX_IMAGE_SIZE,
        AttachmentKind.video: MAX_VIDEO_SIZE,
        AttachmentKind.document: MAX_DOC_SIZE,
    }[kind]


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
