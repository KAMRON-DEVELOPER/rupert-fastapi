from io import BytesIO
from typing import Annotated

from fastapi import Depends, File, HTTPException, Query, UploadFile, status
from PIL import Image

from src.apps.chats.schemas.chat_participant import ChatListUserResponse
from src.apps.shared.schemas import (
    MessageResponse,
    PaginatedResponse,
    paginationDep,
)
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas.user import (
    UserDetailResponse,
    UserSummaryResponse,
    UserUpdateRequest,
)
from src.core.boto3 import (
    delete_objects_from_boto3,
    put_object_to_boto3,
    wipe_objects_from_boto3,
)
from src.core.database import sessionDep
from src.core.exceptions import ValidationException
from src.core.logger import logger
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import authDep

from .router import users_router

settings = get_settings()


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


@users_router.get(
    "/search", response_model=PaginatedResponse[ChatListUserResponse]
)
async def search_users(
    session: sessionDep,
    pagination: paginationDep,
    q: Annotated[str | None, Query(min_length=1)] = None,
):
    return await UsersRepository.search(
        session, query=q, limit=pagination.limit, offset=pagination.offset
    )


@users_router.get("/", response_model=UserDetailResponse | UserSummaryResponse)
async def get_user(
    auth: authDep,
    session: sessionDep,
    summary: Annotated[bool, Query()] = False,
):
    user_id, _, _ = auth

    if summary:
        user = await UsersRepository.get_summary(session, user_id)
        return UserSummaryResponse.model_validate(user)
    else:
        user = await UsersRepository.get_detail(session, user_id)
        return UserDetailResponse.model_validate(user)


async def read_validated_image(
    file: UploadFile,
    *,
    field_name: str,
    require_square: bool = False,
    max_width: int,
    max_size_mb: int = 8,
) -> tuple[bytes, str]:
    # file_extension = get_file_extension(file)

    # if file_extension not in allowed_image_extensions:
    #     extensions = ", ".join(allowed_image_extensions)
    #     raise ValidationException(
    #         detail=f"{extensions} formats are allowed for {field_name}"
    #     )

    image_bytes = await file.read()

    width, height = get_image_dimensions(image_bytes)

    if require_square and width != height:
        raise ValidationException(
            detail=f"Width and height of the {field_name} image must be equal."
        )

    if width > max_width:
        raise ValidationException(
            detail=f"{field_name.capitalize()} image width exceeded limit {max_width}px."
        )

    if len(image_bytes) > max_size_mb * 1024 * 1024:
        raise ValidationException(
            detail=f"{field_name.capitalize()} image size exceeded limit {max_size_mb}MB."
        )

    content_type = file.content_type or "application/octet-stream"

    return image_bytes, content_type


@users_router.patch("/", response_model=MessageResponse)
async def update_user(
    auth: authDep,
    session: sessionDep,
    schm: Annotated[UserUpdateRequest, Depends(UserUpdateRequest.as_form)],
    avatar: Annotated[UploadFile | None, File()] = None,
    banner: Annotated[UploadFile | None, File()] = None,
):
    user_id, _, _ = auth

    values = schm.model_dump(exclude_unset=True)

    avatar_key = f"users/{user_id.hex}/avatar"
    banner_key = f"users/{user_id.hex}/banner"

    avatar_delete_requested = bool(values.pop("delete_avatar", False))
    banner_delete_requested = bool(values.pop("delete_banner", False))

    if avatar_delete_requested:
        await delete_objects_from_boto3([avatar_key])
        values["avatar_url"] = None

    if banner_delete_requested:
        await delete_objects_from_boto3([banner_key])
        values["banner_url"] = None

    if avatar:
        avatar_bytes, content_type = await read_validated_image(
            avatar,
            field_name="avatar",
            require_square=True,
            max_width=2048,
            max_size_mb=8,
        )

        await put_object_to_boto3(
            object_name=avatar_key, data=avatar_bytes, content_type=content_type
        )

        values["avatar_url"] = avatar_key

    if banner:
        banner_bytes, content_type = await read_validated_image(
            banner,
            field_name="banner",
            require_square=False,
            max_width=4096,
            max_size_mb=8,
        )

        await put_object_to_boto3(
            object_name=banner_key, data=banner_bytes, content_type=content_type
        )

        values["banner_url"] = banner_key

    await UsersRepository.update(session, user_id, values)
    await session.commit()
    return MessageResponse(message="User updated successfully")


@users_router.delete(
    "/", response_model=None, status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(auth: authDep, session: sessionDep):
    user_id, _, refresh_token = auth

    await SessionsRepository.delete(session, user_id, refresh_token)
    await UsersRepository.delete(session, user_id)
    await session.commit()

    await wipe_objects_from_boto3(user_id=user_id.hex)
