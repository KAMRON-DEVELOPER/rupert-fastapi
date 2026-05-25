from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.schemas.enums import ChatEvent
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

@chats_router.websocket("/{chat_id}/ws")
async def chat_ws(
    session: sessionDep, websocket: WebSocket, auth: authDep, chat_id: UUID
):
    raw_user_id, _, _ = auth
    user_id = UserId(str(raw_user_id))

    try:
        # TODO: assert user_id is a participant of chat_id
        pass
    except Exception as e:
        logger.error("[chat_ws] authorization failed: %s", e)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    websocket.state.session = session
    websocket.state.user_id = user_id
    websocket.state.chat_id = chat_id

    channels = {chat_channel(chat_id), user_channel(user_id)}

    handlers: dict[ChatEvent, WebSocketHandler] = {
        ChatEvent.ping: handle_ping,
        ChatEvent.typing_start: handle_typing_start,
        ChatEvent.typing_stop: handle_typing_stop,
        ChatEvent.sent_message: handle_sent_message,
        ChatEvent.created_chat: handle_created_chat,
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
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await broker.publish(
        chat_channel(chat_id),
        {"type": ChatEvent.goes_online.value, "user_id": user_id},
        exclude=connection_id,
    )


async def disconnect_handler(
    websocket: WebSocket, connection_id: ConnectionId, broker: EventBroker
) -> None:
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await broker.publish(
        chat_channel(chat_id),
        {"type": ChatEvent.goes_offline.value, "user_id": user_id},
        exclude=connection_id,
    )


async def handle_ping(
    _websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    _payload: dict[str, Any],
) -> None:
    await broker.send(connection_id, {"type": "pong"})


async def handle_typing_start(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    _payload: dict[str, Any],
) -> None:
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await broker.publish(
        chat_channel(chat_id),
        {"type": ChatEvent.typing_start.value, "user_id": user_id},
        exclude=connection_id,
    )


async def handle_typing_stop(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    _payload: dict[str, Any],
) -> None:
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await broker.publish(
        chat_channel(chat_id),
        {"type": ChatEvent.typing_stop.value, "user_id": user_id},
        exclude=connection_id,
    )


async def handle_sent_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    _session: AsyncSession = websocket.state.session
    chat_id: UUID = websocket.state.chat_id
    user_id: UserId = websocket.state.user_id

    message = payload.get("message")
    if not isinstance(message, str):
        await broker.send(
            connection_id,
            {
                "type": ChatEvent.error.value,
                "detail": "message type must be string",
            },
        )
        return

    # TODO: save message to DB here

    await broker.publish(
        chat_channel(chat_id),
        {
            "type": ChatEvent.sent_message.value,
            "sender_id": user_id,
            "message": message.strip(),
            "chat_id": chat_id,
        },
    )


async def handle_created_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    _session: AsyncSession = websocket.state.session
    chat_id: UUID = websocket.state.chat_id
    user_id: UserId = websocket.state.user_id

    message = payload.get("message")
    if not isinstance(message, str):
        await broker.send(
            connection_id,
            {
                "type": ChatEvent.error.value,
                "detail": "message type must be string",
            },
        )
        return

    # TODO: created chat event to DB here / save initial chat message

    await broker.publish(
        chat_channel(chat_id),
        {
            "type": ChatEvent.created_chat.value,
            "sender_id": user_id,
            "message": message.strip(),
            "chat_id": chat_id,
        },
    )
