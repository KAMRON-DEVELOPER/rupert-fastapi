from typing import Annotated
from uuid import UUID

from fastapi import Body, File, Path, Query, UploadFile, status

from apps.chats.models import ChatMessageModel
from src.apps.chats.repositories.chat_message import ChatMessageRepository
from src.apps.chats.schemas.chat_message import ChatMessageResponse
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import chats_router


@chats_router.post(
    "/{chat_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_message(
    session: sessionDep,
    auth: authDep,
    message: Annotated[
        str | None, Body(min_length=1, max_length=10_000)
    ] = None,
    reply_id: Annotated[UUID | None, Body()] = None,
    images: Annotated[list[UploadFile] | None, File()] = None,
    videos: Annotated[list[UploadFile] | None, File()] = None,
    chat_id: Annotated[
        UUID | None, Path(title="None means new chat should be created")
    ] = None,
    participant_id: Annotated[
        UUID | None,
        Query(title="None means new chat participant should be created"),
    ] = None,
):
    user_id, _, _ = auth

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
            object_name=avatar_key,
            data=avatar_bytes,
            content_type=content_type,
        )

        values["avatar_url"] = avatar_key

    message = await ChatMessageRepository.create(
        session=session,
        sender_id=user_id,
        chat_id=chat_id,
        participant_id=participant_id,
        reply_id=reply_id,
        message=message,
        image_urls=image_urls,
        video_urls=video_urls,
    )
    await session.commit()
    return ChatMessageResponse.model_validate(message)


@chats_router.get(
    "/{chat_id}/messages",
    response_model=PaginatedResponse[ChatMessageModel],
)
async def list_chat_messages(
    session: sessionDep,
    auth: authDep,
    pagination: paginationDep,
    chat_id: UUID,
):
    user_id, _, _ = auth
    return await ChatMessageRepository.get_many(
        session=session,
        chat_id=chat_id,
        user_id=user_id,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@chats_router.delete("/{chat_id}/messages/{message_id}")
async def delete_chat_message(
    session: sessionDep,
    auth: authDep,
    chat_id: UUID,
    message_id: UUID,
):
    user_id, _, _ = auth
    await ChatMessageRepository.delete(session, user_id, chat_id, message_id)
    await session.commit()
