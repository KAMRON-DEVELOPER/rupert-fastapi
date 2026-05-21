import json
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from src.apps.shared.schemas.enums import ChatEvent
from src.core.logger import logger

WebSocketHandler = Callable[[str, dict[str, Any]], Awaitable[None]]


class WebSocketManager:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self.user_rooms: dict[str, set[str]] = defaultdict(set)

    async def connect(self, user_id: str, room: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms[room].add(websocket)
        self.user_rooms[user_id].add(room)

    async def disconnect(self, user_id: str, room: str, websocket: WebSocket):
        connections = self.rooms.get(room)
        if connections:
            connections.discard(websocket)
            if not connections:
                self.rooms.pop(room, None)

        rooms = self.user_rooms.get(user_id)
        if rooms:
            rooms.discard(room)
            if not rooms:
                self.user_rooms.pop(user_id, None)

    async def send_personal_message(
        self, websocket: WebSocket, data: dict[str, Any]
    ):
        await websocket.send_json(data)

    async def broadcast(
        self,
        room: str,
        data: dict[str, Any],
        exclude: WebSocket | None = None,
    ):
        for websocket in list(self.rooms.get(room, set())):
            if websocket is exclude:
                continue

            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"[WebSocketManager] broadcast: {e}")
                self.rooms[room].discard(websocket)

    def room_size(self, room: str) -> int:
        return len(self.rooms.get(room, set()))


class WebSocketContextManager:
    def __init__(
        self,
        websocket: WebSocket,
        user_id: str,
        connect_handler: Callable[[str, WebSocket], Awaitable[None]],
        disconnect_handler: Callable[[str, WebSocket], Awaitable[None]],
        message_handlers: dict[ChatEvent, WebSocketHandler],
    ):
        self.websocket = websocket
        self.user_id = user_id
        self.connect_handler = connect_handler
        self.disconnect_handler = disconnect_handler
        self.message_handlers = message_handlers

    async def __aenter__(self):
        await self.connect_handler(self.user_id, self.websocket)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect_handler(self.user_id, self.websocket)

    async def wait_until_disconnected(self):
        try:
            async for text in self.websocket.iter_text():
                await self._handle_text(text)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"[WebSocketContextManager] receiver: {e}")

    async def _handle_text(self, text: str):
        try:
            data: dict = json.loads(text)
        except json.JSONDecodeError:
            await self.websocket.send_json(
                {"type": "error", "detail": "invalid json"}
            )
            return

        event_type: str | None = data.get("type")

        if not event_type:
            logger.warning(
                f"[_handle_text] missing 'type' field in event data: {data}"
            )
            await self.websocket.send_json(
                {
                    "type": "error",
                    "detail": "Missing event type in message.",
                }
            )
            return

        try:
            chat_event = ChatEvent(event_type)
        except ValueError:
            logger.warning(f"Invalid event type received: '{event_type}'")
            await self.websocket.send_json(
                {"type": "error", "detail": "unknown message type"}
            )
            return

        handler = self.message_handlers.get(chat_event)

        if not handler:
            await self.websocket.send_json(
                {"type": "error", "detail": "unknown message type"}
            )
            return

        data["websocket"] = self.websocket
        await handler(self.user_id, data)


websocket_manager = WebSocketManager()
