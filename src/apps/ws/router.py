from fastapi import APIRouter, WebSocket

from src.apps.shared.schemas.enums import IncomingEvent
from src.apps.ws.handlers.incoming.chat import (
    handle_clear_chat,
    handle_create_chat,
    handle_delete_chat,
    handle_delete_message,
    handle_join_chat,
    handle_leave_chat,
    handle_ping,
    handle_read_chat,
    handle_send_message,
    handle_typing_start,
    handle_typing_stop,
    handle_update_chat_settings,
    handle_update_message,
)
from src.apps.ws.helpers import set_websocket_state
from src.apps.ws.lifecycle import connect_handler, disconnect_handler
from src.core.database import sessionDep
from src.core.settings import get_settings
from src.core.websocket.broker import event_broker
from src.core.websocket.channels import user_channel
from src.core.websocket.connection import WebSocketConnection, WebSocketHandler
from src.core.websocket.registry import connection_registry
from src.core.websocket.types import UserId
from src.dependencies.proactive_refresh import authDep

ws_router = APIRouter()


settings = get_settings()

handlers: dict[IncomingEvent, WebSocketHandler] = {
    IncomingEvent.ping: handle_ping,
    IncomingEvent.join_chat: handle_join_chat,
    IncomingEvent.leave_chat: handle_leave_chat,
    IncomingEvent.typing_start: handle_typing_start,
    IncomingEvent.typing_stop: handle_typing_stop,
    IncomingEvent.create_chat: handle_create_chat,
    IncomingEvent.send_message: handle_send_message,
    IncomingEvent.update_message: handle_update_message,
    IncomingEvent.delete_message: handle_delete_message,
    IncomingEvent.read_chat: handle_read_chat,
    IncomingEvent.clear_chat: handle_clear_chat,
    IncomingEvent.delete_chat: handle_delete_chat,
    IncomingEvent.update_chat_settings: handle_update_chat_settings,
}


@ws_router.websocket("/")
async def chat_ws(websocket: WebSocket, session: sessionDep, auth: authDep):
    user_uuid, _, _ = auth
    user_id = UserId(str(user_uuid))

    set_websocket_state(websocket, session, user_uuid, user_id)

    channels = {user_channel(user_id)}

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
