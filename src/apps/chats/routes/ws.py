from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException, WebSocket
from pydantic import Field, ValidationError, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.repositories.chat_message import ChatMessageRepository
from src.apps.chats.repositories.chat_participant import (
    ChatParticipantRepository,
)
from src.apps.chats.schemas.chat import CreateChatSchema
from src.apps.chats.schemas.chat_message import (
    CreateChatMessageRequest,
    UpdateChatMessageRequest,
)
from src.apps.chats.schemas.chat_participant import ChatSettingsRequest
from src.apps.shared.schemas.base import RequestSchema, ResponseSchema
from src.apps.shared.schemas.enums import ChatEvent
from src.core.boto3 import (
    delete_objects_from_boto3,
    remove_pending_tags_from_s3,
)
from src.core.database import sessionDep
from src.core.logger import logger
from src.core.settings import get_settings
from src.core.websocket.broker import EventBroker, event_broker
from src.core.websocket.channels import chat_channel, user_channel
from src.core.websocket.connection import WebSocketConnection, WebSocketHandler
from src.core.websocket.registry import connection_registry
from src.core.websocket.types import ConnectionId, UserId
from src.dependencies.proactive_refresh import authDep

from .router import chats_router

settings = get_settings()


TRequest = TypeVar("TRequest", bound=RequestSchema)
Action = Callable[[], Awaitable[None]]


class ChatRoomActionRequest(RequestSchema):
    chat_id: UUID


class MessageActionRequest(ChatRoomActionRequest):
    message_id: UUID


class ReadChatRequest(ChatRoomActionRequest):
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScopedChatActionRequest(ChatRoomActionRequest):
    for_participant: bool = False


class UpdateChatSettingsActionRequest(ChatSettingsRequest):
    chat_id: UUID

    @model_validator(mode="after")
    def validate_values(self):
        if (
            self.is_pinned is None
            and self.is_muted is None
            and self.is_archived is None
        ):
            raise ValueError("at least one chat setting is required")
        return self


class UpdateMessageActionRequest(UpdateChatMessageRequest):
    chat_id: UUID
    message_id: UUID


@chats_router.websocket("/ws")
async def chat_ws(websocket: WebSocket, session: sessionDep, auth: authDep):
    raw_user_id, _, _ = auth
    user_id = UserId(str(raw_user_id))

    websocket.state.session = session
    websocket.state.user_id = user_id
    websocket.state.user_uuid = raw_user_id
    websocket.state.chat_ids = set()

    channels = {user_channel(user_id)}

    handlers: dict[ChatEvent, WebSocketHandler] = {
        ChatEvent.ping: handle_ping,
        ChatEvent.join_chat: handle_join_chat,
        ChatEvent.leave_chat: handle_leave_chat,
        ChatEvent.typing_start: handle_typing_start,
        ChatEvent.typing_stop: handle_typing_stop,
        ChatEvent.create_chat: handle_create_chat,
        ChatEvent.send_message: handle_send_message,
        ChatEvent.update_message: handle_update_message,
        ChatEvent.delete_message: handle_delete_message,
        ChatEvent.read_chat: handle_read_chat,
        ChatEvent.clear_chat: handle_clear_chat,
        ChatEvent.delete_chat: handle_delete_chat,
        ChatEvent.update_chat_settings: handle_update_chat_settings,
    }

    async with WebSocketConnection(
        websocket=websocket,
        user_id=user_id,
        channels=channels,
        handlers=handlers,
        registry=connection_registry,
        broker=event_broker,
        connect_handler=connect_handler,
        disconnect_handler=disconnect_handler,
    ) as conn:
        await conn.run_until_disconnect()


async def connect_handler(
    websocket: WebSocket, connection_id: ConnectionId, broker: EventBroker
) -> None:
    session, user_uuid, user_id = _context(websocket)
    if connection_registry.user_has_connection(user_id, exclude=connection_id):
        return

    participant_ids = await ChatRepository.get_participant_ids(
        session, user_uuid
    )
    await _publish_to_users(
        broker,
        participant_ids,
        _event(ChatEvent.user_online, user_id=user_uuid),
    )


async def disconnect_handler(
    websocket: WebSocket, connection_id: ConnectionId, broker: EventBroker
) -> None:
    session, user_uuid, user_id = _context(websocket)
    chat_ids: set[UUID] = websocket.state.chat_ids

    for chat_id in chat_ids:
        await _leave_chat_channel(
            websocket=websocket,
            connection_id=connection_id,
            broker=broker,
            chat_id=chat_id,
            notify_self=False,
        )

    if connection_registry.user_has_connection(user_id, exclude=connection_id):
        logger.debug("[chat_ws] disconnected user=%s", user_id)
        return

    last_online_at = datetime.now(UTC)
    try:
        await ChatParticipantRepository.set_last_online_at(
            session, user_uuid, last_online_at
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, user_uuid
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("[chat_ws] disconnect presence update failed: %s", e)
        return

    await _publish_to_users(
        broker,
        participant_ids,
        _event(
            ChatEvent.user_offline,
            user_id=user_uuid,
            last_online_at=last_online_at,
        ),
    )
    logger.debug("[chat_ws] disconnected user=%s", user_id)


async def handle_ping(
    _websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    _payload: dict[str, Any],
) -> None:
    await broker.send(connection_id, _event(ChatEvent.pong))


async def handle_join_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(ChatRoomActionRequest, payload)
        session, user_uuid, _ = _context(websocket)
        channel = chat_channel(data.chat_id)

        await ChatRepository.assert_participant(
            session, data.chat_id, user_uuid
        )
        connection_registry.join_channel(connection_id, channel)
        websocket.state.chat_ids.add(data.chat_id)

        await broker.send(
            connection_id, _event(ChatEvent.chat_joined, chat_id=data.chat_id)
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_leave_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(ChatRoomActionRequest, payload)
        await _leave_chat_channel(
            websocket=websocket,
            connection_id=connection_id,
            broker=broker,
            chat_id=data.chat_id,
            notify_self=True,
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_typing_start(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    await _publish_typing(
        websocket, connection_id, broker, payload, ChatEvent.typing_start
    )


async def handle_typing_stop(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    await _publish_typing(
        websocket, connection_id, broker, payload, ChatEvent.typing_stop
    )


async def handle_create_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(CreateChatSchema, payload)
        session, user_uuid, _ = _context(websocket)

        chat = await ChatRepository.get_or_create_direct_chat(
            session, user_uuid, data.participant_id
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, chat.id
        )
        await session.commit()

        # TODO we might send ChatListItemResponse directly
        # so frontend does not need to refetch or invalidate cache
        event = _event(
            ChatEvent.chat_created,
            chat_id=chat.id,
            participant_id=data.participant_id,
        )
        await _publish_to_users(broker, participant_ids, event)

    await _guard(websocket, connection_id, broker, action)


async def handle_send_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(CreateChatMessageRequest, payload)
        session, user_uuid, _ = _context(websocket)

        record = await ChatMessageRepository.create(
            session,
            user_uuid,
            message=data.message,
            chat_id=data.chat_id,
            reply_id=data.reply_id,
            participant_id=data.participant_id,
            attachments=data.attachments,
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, record.chat_id
        )
        new_keys = _message_attachment_keys(record)
        message = ChatMessageRepository.to_response(record)
        await session.commit()

        await _remove_pending_tags(new_keys)
        await _publish_to_users(
            broker,
            participant_ids,
            _event(ChatEvent.message_created, message=message),
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_update_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(UpdateMessageActionRequest, payload)
        session, user_uuid, _ = _context(websocket)

        record, old_keys, new_keys = await ChatMessageRepository.update(
            session,
            user_uuid,
            data.message_id,
            chat_id=data.chat_id,
            message=data.message,
            attachments=data.attachments,
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, record.chat_id
        )
        message = ChatMessageRepository.to_response(record)
        await session.commit()

        await _remove_pending_tags(new_keys)
        await _delete_objects(old_keys)
        await _publish_to_users(
            broker,
            participant_ids,
            _event(ChatEvent.message_updated, message=message),
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_delete_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(MessageActionRequest, payload)
        session, user_uuid, _ = _context(websocket)

        participant_ids = await ChatRepository.get_participant_ids(
            session, data.chat_id
        )
        object_keys = await ChatMessageRepository.attachment_keys(
            session, data.chat_id, data.message_id
        )
        await ChatMessageRepository.delete(
            session, user_uuid, data.chat_id, data.message_id
        )
        await session.commit()

        await _delete_objects(object_keys)
        await _publish_to_users(
            broker,
            participant_ids,
            _event(
                ChatEvent.message_deleted,
                chat_id=data.chat_id,
                message_id=data.message_id,
            ),
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_read_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(ReadChatRequest, payload)
        session, user_uuid, _ = _context(websocket)

        participant = await ChatParticipantRepository.set_last_seen_at(
            session, user_uuid, data.chat_id, data.last_seen_at
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, data.chat_id
        )
        await session.commit()

        await _publish_to_users(
            broker,
            participant_ids,
            _event(
                ChatEvent.chat_read,
                chat_id=data.chat_id,
                user_id=user_uuid,
                last_seen_at=participant.last_seen_at,
            ),
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_clear_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(ScopedChatActionRequest, payload)
        session, user_uuid, _ = _context(websocket)

        if data.for_participant:
            participant_ids = await ChatRepository.get_participant_ids(
                session, data.chat_id
            )
            cleared_at = await ChatParticipantRepository.clear_for_everyone(
                session, data.chat_id, user_uuid
            )
            object_keys = await ChatMessageRepository.attachment_keys_until(
                session, data.chat_id, cleared_at
            )
            await ChatMessageRepository.delete_until(
                session, data.chat_id, cleared_at
            )
            await session.commit()

            await _delete_objects(object_keys)
            await _publish_to_users(
                broker,
                participant_ids,
                _event(
                    ChatEvent.chat_cleared,
                    chat_id=data.chat_id,
                    user_id=user_uuid,
                    cleared_at=cleared_at,
                    for_participant=True,
                ),
            )
            return

        participant = await ChatParticipantRepository.clear_for_me(
            session, user_uuid, data.chat_id
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            _event(
                ChatEvent.chat_cleared,
                chat_id=data.chat_id,
                user_id=user_uuid,
                cleared_at=participant.cleared_at,
                for_participant=False,
            ),
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_delete_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(ScopedChatActionRequest, payload)
        session, user_uuid, _ = _context(websocket)

        if data.for_participant:
            participant_ids = await ChatRepository.get_participant_ids(
                session, data.chat_id
            )
            object_keys = await ChatRepository.attachment_keys(
                session, data.chat_id
            )
            await ChatRepository.delete_for_everyone(
                session, data.chat_id, user_uuid
            )
            await session.commit()

            await _delete_objects(object_keys)
            await _publish_to_users(
                broker,
                participant_ids,
                _event(
                    ChatEvent.chat_deleted,
                    chat_id=data.chat_id,
                    user_id=user_uuid,
                    for_participant=True,
                ),
            )
            return

        participant = await ChatParticipantRepository.delete_for_me(
            session, data.chat_id, user_uuid
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            _event(
                ChatEvent.chat_deleted,
                chat_id=data.chat_id,
                user_id=user_uuid,
                deleted_at=participant.deleted_at,
                for_participant=False,
            ),
        )

    await _guard(websocket, connection_id, broker, action)


async def handle_update_chat_settings(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = _parse(UpdateChatSettingsActionRequest, payload)
        session, user_uuid, _ = _context(websocket)
        values = data.model_dump(
            include={"is_pinned", "is_muted", "is_archived"}, exclude_none=True
        )

        participant = await ChatParticipantRepository.update_settings(
            session, data.chat_id, user_uuid, values
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            _event(
                ChatEvent.chat_settings_updated,
                chat_id=data.chat_id,
                is_pinned=participant.is_pinned,
                is_muted=participant.is_muted,
                is_archived=participant.is_archived,
            ),
        )

    await _guard(websocket, connection_id, broker, action)


async def _publish_typing(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
    event_type: ChatEvent,
) -> None:
    async def action() -> None:
        data = _parse(ChatRoomActionRequest, payload)
        session, user_uuid, _ = _context(websocket)
        await ChatRepository.assert_participant(
            session, data.chat_id, user_uuid
        )

        await broker.publish(
            chat_channel(data.chat_id),
            _event(event_type, chat_id=data.chat_id, user_id=user_uuid),
            exclude=connection_id,
        )

    await _guard(websocket, connection_id, broker, action)


async def _leave_chat_channel(
    *,
    broker: EventBroker,
    websocket: WebSocket,
    connection_id: ConnectionId,
    chat_id: UUID,
    notify_self: bool,
) -> None:
    channel = chat_channel(chat_id)

    was_joined = chat_id in websocket.state.chat_ids
    if was_joined:
        connection_registry.leave_channel(connection_id, channel)
        websocket.state.chat_ids.discard(chat_id)

    if notify_self:
        await broker.send(
            connection_id, _event(ChatEvent.chat_left, chat_id=chat_id)
        )


async def _guard(
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
        await _send_error(broker, connection_id, _validation_detail(e))
    except HTTPException as e:
        await session.rollback()
        await _send_error(broker, connection_id, e.detail, e.status_code)
    except Exception as e:
        await session.rollback()
        logger.exception("[chat_ws] action failed: %s", e)
        await _send_error(broker, connection_id, "internal server error")


def _parse[TRequest: RequestSchema](
    model: type[TRequest], payload: dict[str, Any]
) -> TRequest:
    data = {key: value for key, value in payload.items() if key != "type"}
    return model.model_validate(data)


def _context(websocket: WebSocket) -> tuple[AsyncSession, UUID, UserId]:
    return (
        websocket.state.session,
        websocket.state.user_uuid,
        websocket.state.user_id,
    )


def _event(event_type: ChatEvent, **payload: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"type": event_type.value}
    for key, value in payload.items():
        data[_camel(key)] = _jsonable(value)
    return data


def _jsonable(value: Any) -> Any:
    if isinstance(value, ResponseSchema):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {
            _camel(str(key)): _jsonable(item) for key, item in value.items()
        }
    return value


def _camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


async def _publish_to_users(
    broker: EventBroker, user_ids: Iterable[UUID], event: dict[str, Any]
) -> None:
    for user_id in user_ids:
        await broker.publish(user_channel(UserId(str(user_id))), event)


async def _send_error(
    broker: EventBroker,
    connection_id: ConnectionId,
    detail: Any,
    status_code: int | None = None,
) -> None:
    payload: dict[str, Any] = {"type": ChatEvent.error.value, "detail": detail}
    if status_code is not None:
        payload["statusCode"] = status_code
    await broker.send(connection_id, payload)


def _validation_detail(error: ValidationError) -> str:
    first = error.errors()[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    message = str(first.get("msg", "invalid payload"))
    return f"{location}: {message}" if location else message


def _message_attachment_keys(record: Any) -> list[str]:
    return [link.attachment.object_key for link in record.attachment_links]


async def _remove_pending_tags(keys: list[str]) -> None:
    if keys:
        await remove_pending_tags_from_s3(keys)


async def _delete_objects(keys: list[str]) -> None:
    if not keys:
        return
    try:
        await delete_objects_from_boto3(keys)
    except HTTPException as e:
        logger.error("[chat_ws] committed DB change, S3 delete failed: %s", e)
