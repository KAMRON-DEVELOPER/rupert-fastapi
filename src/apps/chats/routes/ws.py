from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.schemas.enums import ChatEvent
from src.core.database import sessionDep
from src.core.logger import logger
from src.core.websocket.channels import chat_channel, user_channel
from src.core.websocket.connection import WebSocketConnection, WebSocketHandler
from src.core.websocket.registry import connection_registry
from src.core.websocket.transport.base import WebSocketTransport
from src.core.websocket.transport.local import websocket_transport
from src.core.websocket.types import ConnectionId, UserId
from src.dependencies.proactive_refresh import authDep

from .router import chats_router


@chats_router.websocket("/{chat_id}/ws")
async def chat_ws(
    session: sessionDep,
    websocket: WebSocket,
    auth: authDep,
    chat_id: UUID,
):
    user_id, _, _ = auth
    user_id = UserId(str(user_id))

    try:
        # TODO: authorize the user_id is participant of the chat_id
        pass
    except Exception as e:
        logger.error(f"[chat_ws] authorization failed: {e}")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    websocket.state.session = session
    websocket.state.user_id = user_id
    websocket.state.chat_id = chat_id

    channels = {
        chat_channel(chat_id),
        user_channel(user_id),
    }

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
        transport=websocket_transport,
        connect_handler=connect_handler,
        disconnect_handler=disconnect_handler,
    ) as conn:
        await conn.run_until_disconnect()


async def connect_handler(
    websocket: WebSocket,
    connection_id: ConnectionId,
    transport: WebSocketTransport,
):
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await transport.publish(
        chat_channel(chat_id),
        {
            "type": ChatEvent.goes_online.value,
            "user_id": str(user_id),
        },
        exclude=connection_id,
    )


async def disconnect_handler(
    websocket: WebSocket,
    connection_id: ConnectionId,
    transport: WebSocketTransport,
):
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await transport.publish(
        chat_channel(chat_id),
        {
            "type": ChatEvent.goes_offline.value,
            "user_id": str(user_id),
        },
        exclude=connection_id,
    )


async def handle_ping(
    _websocket: WebSocket,
    connection_id: ConnectionId,
    transport: WebSocketTransport,
    _payload: dict[str, Any],
) -> None:
    await transport.send(connection_id, {"type": "pong"})


async def handle_typing_start(
    websocket: WebSocket,
    connection_id: ConnectionId,
    transport: WebSocketTransport,
    _payload: dict[str, Any],
) -> None:
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await transport.publish(
        chat_channel(chat_id),
        {
            "type": ChatEvent.typing_start.value,
            "user_id": str(user_id),
        },
        exclude=connection_id,
    )


async def handle_typing_stop(
    websocket: WebSocket,
    connection_id: ConnectionId,
    transport: WebSocketTransport,
    _payload: dict[str, Any],
) -> None:
    user_id: UserId = websocket.state.user_id
    chat_id: UUID = websocket.state.chat_id

    await transport.publish(
        chat_channel(chat_id),
        {
            "type": ChatEvent.typing_stop.value,
            "user_id": str(user_id),
        },
        exclude=connection_id,
    )


async def handle_sent_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    transport: WebSocketTransport,
    payload: dict[str, Any],
) -> None:
    _session: AsyncSession = websocket.state.session
    chat_id: UUID = websocket.state.chat_id
    user_id: UserId = websocket.state.user_id

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        await transport.send(
            connection_id,
            {
                "type": ChatEvent.error.value,
                "detail": "message is required",
            },
        )
        return

    # TODO:
    # record = await create_chat_message(
    #     session=session,
    #     chat_id=chat_id,
    #     sender_id=UUID(str(user_id)),
    #     message=message.strip(),
    # )
    # await session.commit()
    # await session.refresh(record)

    event = {
        "type": ChatEvent.sent_message.value,
        "chat_id": str(chat_id),
        "sender_id": str(user_id),
        "message": message.strip(),
    }

    await transport.publish(chat_channel(chat_id), event)


async def handle_created_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    transport: WebSocketTransport,
    payload: dict[str, Any],
) -> None:
    _session: AsyncSession = websocket.state.session
    chat_id: UUID = websocket.state.chat_id
    user_id: UserId = websocket.state.user_id

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        await transport.send(
            connection_id,
            {
                "type": ChatEvent.error.value,
                "detail": "message is required",
            },
        )
        return

    # TODO:
    # record = await create_chat_message(
    #     session=session,
    #     chat_id=chat_id,
    #     sender_id=UUID(str(user_id)),
    #     message=message.strip(),
    # )
    # await session.commit()
    # await session.refresh(record)

    event = {
        "type": ChatEvent.sent_message.value,
        "chat_id": str(chat_id),
        "sender_id": str(user_id),
        "message": message.strip(),
    }

    await transport.publish(chat_channel(chat_id), event)
