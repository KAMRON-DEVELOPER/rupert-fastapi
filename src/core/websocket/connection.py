import json
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from src.apps.shared.schemas.enums import ChatEvent
from src.core.logger import logger

from .registry import ConnectionRegistry
from .transport.base import WebSocketTransport
from .types import Channel, ConnectionId, UserId

WebSocketHandler = Callable[
    [WebSocket, ConnectionId, WebSocketTransport, dict[str, Any]],
    Awaitable[None],
]

WebSocketLifecycleHandler = Callable[
    [WebSocket, ConnectionId, WebSocketTransport], Awaitable[None]
]


class WebSocketConnection:
    """
    Boss of one live WebSocket connection.

    Role:
    - accept socket
    - register connection
    - subscribe initial channels
    - call connect handler
    - run receive loop
    - parse JSON
    - dispatch handlers
    - call disconnect handler
    - cleanup registry
    - close socket

    This is the top-level WebSocket engine.
    """

    def __init__(
        self,
        *,
        websocket: WebSocket,
        user_id: UserId,
        channels: set[Channel],
        handlers: dict[ChatEvent, WebSocketHandler],
        registry: ConnectionRegistry,
        transport: WebSocketTransport,
        connect_handler: WebSocketLifecycleHandler | None = None,
        disconnect_handler: WebSocketLifecycleHandler | None = None,
    ) -> None:
        self.websocket = websocket
        self.user_id = user_id
        self.channels = channels
        self.handlers = handlers
        self.registry = registry
        self.transport = transport
        self.connect_handler = connect_handler
        self.disconnect_handler = disconnect_handler

        self.connection_id: ConnectionId | None = None

    async def __aenter__(self) -> "WebSocketConnection":
        await self.websocket.accept()

        self.connection_id = self.registry.add_connection(
            websocket=self.websocket, user_id=self.user_id
        )

        for channel in self.channels:
            self.registry.subscribe(self.connection_id, channel)

        if self.connect_handler is not None:
            await self.connect_handler(
                self.websocket, self.connection_id, self.transport
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.connection_id is None:
            return

        try:
            if self.disconnect_handler is not None:
                await self.disconnect_handler(
                    self.websocket, self.connection_id, self.transport
                )
        finally:
            websocket = self.registry.remove_connection(self.connection_id)

            if (
                websocket is not None
                and websocket.client_state == WebSocketState.CONNECTED
            ):
                try:
                    await websocket.close()
                except Exception:
                    pass

    async def run_until_disconnect(self) -> None:
        try:
            async for text in self.websocket.iter_text():
                await self._process_text(text)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.exception("[WebSocketConnection] failed: %s", e)

    async def _process_text(self, text: str) -> None:
        if self.connection_id is None:
            return

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            await self.transport.send(
                self.connection_id,
                {
                    "type": ChatEvent.error.value,
                    "detail": "invalid json",
                },
            )
            return

        if not isinstance(payload, dict):
            await self.transport.send(
                self.connection_id,
                {
                    "type": ChatEvent.error.value,
                    "detail": "payload must be object",
                },
            )
            return

        event_type = payload.get("type")
        if not isinstance(event_type, str):
            await self.transport.send(
                self.connection_id,
                {
                    "type": ChatEvent.error.value,
                    "detail": "missing event type",
                },
            )
            return

        try:
            event = ChatEvent(event_type)
        except ValueError:
            await self.transport.send(
                self.connection_id,
                {
                    "type": ChatEvent.error.value,
                    "detail": "unknown event type",
                },
            )
            return

        handler = self.handlers.get(event)
        if handler is None:
            await self.transport.send(
                self.connection_id,
                {
                    "type": ChatEvent.error.value,
                    "detail": "no handler for event",
                },
            )
            return

        await handler(
            self.websocket, self.connection_id, self.transport, payload
        )
