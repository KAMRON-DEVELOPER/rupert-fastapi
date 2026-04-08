import mimetypes
import random
import re
import string
from io import BytesIO
from uuid import UUID

import aiohttp
from PIL import Image

from src.utils.logger import logger
from src.utils.minio import put_object_to_minio


def generate_username_from_base_name(base_name: str) -> str:
    return re.sub(pattern=r"[^a-zA-Z0-9_]", repl="", string=base_name.lower().replace(" ", "_"))


def generate_random_name(max_length: int = 14) -> str:
    if max_length < 5:
        raise ValueError("max_length must be at least 5")

    while True:
        first_len = random.randint(2, max_length // 2 - 1)
        second_len = random.randint(2, max_length - first_len - 1)

        first_word = random.choice(string.ascii_uppercase) + "".join(random.choices(string.ascii_lowercase, k=first_len - 1))
        second_word = random.choice(string.ascii_uppercase) + "".join(random.choices(string.ascii_lowercase, k=second_len - 1))

        full_name = f"{first_word} {second_word}"
        if len(full_name) <= max_length:
            return full_name


def generate_random_username(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_password_string() -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for _ in range(12))
    return password


async def download_image(image_url: str) -> tuple[bytes, str, str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download image from {image_url}")
                image_data = await response.read()

                if not image_data:
                    raise ValueError("Downloaded image is empty.")

                image_stream = BytesIO(image_data)  # noqa
                try:
                    with Image.open(image_stream) as img:
                        extension = img.format.lower() if img.format else ""
                except Exception as e:
                    raise ValueError(f"Couldn't get image extension. {e}")

                # Get the content type
                content_type = mimetypes.types_map.get(f".{extension}", "application/octet-stream")

                return image_data, extension, content_type
    except Exception as e:
        print(f"🌋 Exception in download_image: {e}")
        raise Exception("🌋 Exception in download_image")


async def prepare_image_data(image_data: bytes, max_width: int = 72, max_height: int = 72) -> BytesIO:
    try:
        # Open the image using BytesIO
        print(f"🔨 2 Uploading image of size {len(image_data)} bytes to MinIO.")
        image_stream = BytesIO(image_data)  # noqa
        pil_image = Image.open(image_stream)

        # Verify and convert to RGB in a single step
        pil_image.load()  # Ensure the image is loaded
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Resize the image while maintaining aspect ratio
        pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Save into output BytesIO
        output_image = BytesIO()
        pil_image.save(output_image, format="PNG", quality=85)
        output_image.seek(0)

        return output_image
    except Exception as e:
        print(f"🌋 Exception in prepare_image_data: {e}")
        raise ValueError(f"🌋 Exception in prepare_image_data: {e}")


async def generate_avatar_url(user_id: UUID, image_url: str) -> str | None:
    print(f"🚧 image_url: {image_url}, user_id: {user_id}")

    try:
        image_data, extension, content_type = await download_image(image_url=image_url)
        logger.debug(f"generate_avatar_url len(image_data): {len(image_data)}, extension: {extension}")
        if image_data:
            image_stream: BytesIO = await prepare_image_data(image_data=image_data)
            image_data: bytes = image_stream.read()
            if image_data:
                print(f"🔨 3 Uploading image of size {len(image_data)} bytes to MinIO.")
                print(f"🔨 4 Uploading image of size {len(image_stream.getbuffer())} bytes to MinIO.")
                uploaded_object = await put_object_to_minio(
                    object_name=f"users/{user_id.hex}/avatar.{extension}",
                    data=image_data,
                    content_type=content_type,
                )
                if uploaded_object:
                    print(f"✅ Successfully uploaded image to MinIO: {uploaded_object}")
                return uploaded_object
        return None
    except Exception as e:
        print(f"🌋 Exception in generate_avatar_url: {e}")
        raise ValueError(f"🌋 Exception in generate_avatar_url: {e}")
