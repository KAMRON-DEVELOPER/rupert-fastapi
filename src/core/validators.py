import json
import re
import subprocess
import uuid
from datetime import datetime
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from src.core.exceptions import ValidationException
from src.core.logger import logger

email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
violent_words = [
    "sex",
    "sexy",
    "sexual",
    "nude",
    "porn",
    "pornography",
    "nudes",
    "nudity",
]
violent_words_regex = (
    r"(" + "|".join(re.escape(word) for word in violent_words) + r")"
)
allowed_image_extensions = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "svg",
    "webp",
    "avif",
    "apng",
}
allowed_video_extension = {"mp4", "webm", "ogg", "ogv", "mov", "avi", "mkv"}


def validate_username(username: str | None = None) -> None:
    if username is not None:
        if not username:
            raise ValidationException(detail="Username cannot be empty.")
        validate_length(
            field=username, min_len=3, max_len=20, field_name="Username"
        )
        if re.search(violent_words_regex, username, re.IGNORECASE):
            raise ValidationException(
                "Username contains restricted or inappropriate content."
            )


def validate_email(email: str | None = None) -> None:
    if email is not None:
        if not email:
            raise ValidationException(detail="Email cannot be empty.")
        validate_length(field=email, min_len=5, max_len=255, field_name="Email")
        if not re.match(email_regex, email):
            raise ValidationException("Invalid email format.")


def validate_phone_number(phone_number: str | None = None):
    if phone_number is not None:
        if not phone_number:
            raise ValidationException(detail="Phone number cannot be empty.")


def validate_password(password_string: str | None = None) -> None:
    if password_string is not None:
        if not password_string:
            raise ValidationException(detail="Password cannot be empty.")
        validate_length(
            field=password_string, min_len=8, max_len=255, field_name="Password"
        )
        if not re.search(pattern=r"\d", string=password_string):
            raise ValidationException(
                "Password must contain at least one digit."
            )
        if not re.search(pattern=r"[a-zA-Z]", string=password_string):
            raise ValidationException(
                "Password must contain at least one letter."
            )


def validate_length(field: str, min_len: int, max_len: int, field_name: str):
    if not (min_len <= len(field) <= max_len):
        raise ValidationException(
            f"{field_name} must be between {min_len} and {max_len} characters."
        )


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


def convert_for_redis(data: dict) -> dict:
    """Convert UUID to hex and datetime to ISO format for Redis compatibility."""

    def convert_value(value):
        if isinstance(value, uuid.UUID):
            return value.hex
        elif isinstance(value, datetime):
            return value.timestamp()
        elif isinstance(value, dict):
            return convert_for_redis(value)
        elif isinstance(value, (list, tuple)):
            return [convert_value(v) for v in value]
        return value

    return {key: convert_value(value) for key, value in data.items()}
