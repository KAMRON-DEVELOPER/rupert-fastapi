from collections.abc import Iterable
from typing import Any
from uuid import UUID

from fastapi import HTTPException, WebSocket
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.chats.repositories.chat import ChatRepository
from src.apps.shared.schemas.enums import OutgoingEvent
from src.apps.ws.helpers import get_websocket_state
from src.apps.ws.schemas.chat import Action, ChatRoomActionRequest
from src.core.boto3 import (
    delete_objects_from_boto3,
    remove_pending_tags_from_s3,
)
from src.core.logger import logger
from src.core.websocket.broker import EventBroker
from src.core.websocket.channels import chat_channel, user_channel
from src.core.websocket.registry import connection_registry
from src.core.websocket.types import ConnectionId, UserId


async def publish_typing(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
    event_type: OutgoingEvent,
) -> None:
    async def action() -> None:
        data = ChatRoomActionRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)
        await ChatRepository.assert_participant(
            session, data.chat_id, user_uuid
        )

        await broker.publish(
            chat_channel(data.chat_id),
            {
                "type": event_type.value,
                "chatId": data.chat_id,
                "userId": user_uuid,
            },
            exclude=connection_id,
        )

    await guard(websocket, connection_id, broker, action)


async def leave_chat_channel(
    *,
    broker: EventBroker,
    websocket: WebSocket,
    connection_id: ConnectionId,
    chat_id: UUID,
    notify_self: bool,
) -> None:
    channel = chat_channel(chat_id)

    _, _, _, chat_ids = get_websocket_state(websocket)
    was_joined = chat_id in chat_ids
    if was_joined:
        connection_registry.leave_channel(connection_id, channel)
        websocket.state.chat_ids.discard(chat_id)

    if notify_self:
        await broker.send(
            connection_id,
            {"type": OutgoingEvent.chat_left.value, "chatId": chat_id},
        )


async def guard(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    action: Action,
) -> None:
    session: AsyncSession = websocket.state.session
    try:
        await action()
    except ValidationError as e:
        await session.rollback()
        await send_error(broker, connection_id, validation_detail(e))
    except HTTPException as e:
        await session.rollback()
        await send_error(broker, connection_id, e.detail, e.status_code)
    except Exception as e:
        await session.rollback()
        logger.exception(f"[chat_ws] action failed: {e}")
        await send_error(broker, connection_id, "internal server error")


async def publish_to_users(
    broker: EventBroker, user_ids: Iterable[UUID], event: dict[str, Any]
) -> None:
    for user_id in user_ids:
        logger.debug(f"user_id: {user_id}, event: {event}")
        await broker.publish(user_channel(UserId(str(user_id))), event)


async def send_error(
    broker: EventBroker,
    connection_id: ConnectionId,
    detail: Any,
    status_code: int | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": OutgoingEvent.error.value,
        "detail": detail,
    }
    if status_code is not None:
        payload["statusCode"] = status_code
    await broker.send(connection_id, payload)


def validation_detail(error: ValidationError) -> str:
    first = error.errors()[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    message = str(first.get("msg", "invalid payload"))
    return f"{location}: {message}" if location else message


def message_attachment_keys(record: Any) -> list[str]:
    return [link.attachment.object_key for link in record.attachment_links]


async def remove_pending_tags(keys: list[str]) -> None:
    if keys:
        await remove_pending_tags_from_s3(keys)


async def delete_objects(keys: list[str]) -> None:
    if not keys:
        return
    try:
        await delete_objects_from_boto3(keys)
    except HTTPException as e:
        logger.error(f"[chat_ws] committed DB change, S3 delete failed: {e}")
