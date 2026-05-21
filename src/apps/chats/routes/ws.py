from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketException, status

from src.apps.shared.schemas.enums import ChatEvent
from src.core.database import sessionDep
from src.core.logger import logger
from src.core.websocket_manager import (
    WebSocketContextManager,
    websocket_manager,
)
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

    try:
        pass
    except Exception as e:
        logger.error(f"[chat_ws] authorization: {e}")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    websocket.state.chat_id = chat_id
    websocket.state.session = session

    message_handlers = {
        ChatEvent.goes_online: handle_goes_online,
        ChatEvent.goes_offline: handle_goes_offline,
        ChatEvent.typing_start: handle_typing_start,
        ChatEvent.typing_stop: handle_typing_stop,
        ChatEvent.sent_message: handle_sent_message,
        ChatEvent.created_chat: handle_created_chat,
        ChatEvent.ping: handle_ping,
    }

    async with WebSocketContextManager(
        websocket=websocket,
        user_id=str(user_id),
        connect_handler=chat_connect,
        disconnect_handler=chat_disconnect,
        message_handlers=message_handlers,
    ) as connection:
        await connection.wait_until_disconnected()


async def chat_connect(user_id: str, websocket: WebSocket):
    room = _get_room(websocket)
    await websocket_manager.connect(user_id, room, websocket)
    await handle_goes_online(
        user_id, {"type": "goes_online", "websocket": websocket}
    )


async def chat_disconnect(user_id: str, websocket: WebSocket):
    await handle_goes_offline(
        user_id, {"type": "goes_offline", "websocket": websocket}
    )
    await websocket_manager.disconnect(user_id, _get_room(websocket), websocket)


async def handle_goes_online(user_id: str, data: dict[str, Any]):
    websocket = _get_websocket(data)
    await websocket_manager.broadcast(
        _get_room(websocket),
        {"type": ChatEvent.goes_online.value, "user_id": user_id},
        exclude=websocket,
    )


async def handle_goes_offline(user_id: str, data: dict[str, Any]):
    websocket = _get_websocket(data)
    await websocket_manager.broadcast(
        _get_room(websocket),
        {"type": ChatEvent.goes_offline.value, "user_id": user_id},
        exclude=websocket,
    )


async def handle_typing_start(user_id: str, data: dict[str, Any]):
    websocket = _get_websocket(data)
    await websocket_manager.broadcast(
        _get_room(websocket),
        {"type": ChatEvent.typing_start.value, "user_id": user_id},
        exclude=websocket,
    )


async def handle_typing_stop(user_id: str, data: dict[str, Any]):
    websocket = _get_websocket(data)
    await websocket_manager.broadcast(
        _get_room(websocket),
        {"type": ChatEvent.typing_stop.value, "user_id": user_id},
        exclude=websocket,
    )


async def handle_sent_message(user_id: str, data: dict[str, Any]):
    websocket = _get_websocket(data)
    session = websocket.state.session
    chat_id = websocket.state.chat_id
    message = data.get("message") or data.get("content")

    if not message:
        await websocket_manager.send_personal_message(
            websocket, {"type": "error", "detail": "message is required"}
        )
        return

    # record = await _create_message(
    #     session=session,
    #     chat_id=chat_id,
    #     sender_id=UUID(user_id),
    #     message=message,
    # )
    # await session.commit()

    # res = _serialize_message(record)
    # await websocket_manager.broadcast(
    #     _get_room(websocket),
    #     {"type": ChatEvent.sent_message.value, **res.model_dump(mode="json")},
    # )


async def handle_created_chat(user_id: str, data: dict[str, Any]):
    websocket = _get_websocket(data)
    await websocket_manager.broadcast(
        _get_room(websocket),
        {"type": ChatEvent.created_chat.value, "user_id": user_id},
        exclude=websocket,
    )


async def handle_ping(_: str, data: dict[str, Any]):
    websocket = _get_websocket(data)
    await websocket_manager.send_personal_message(websocket, {"type": "pong"})


def _get_room(websocket: WebSocket) -> str:
    return NotImplemented
    # return _chat_room(websocket.state.chat_id)


def _get_websocket(data: dict[str, Any]) -> WebSocket:
    return data["websocket"]
