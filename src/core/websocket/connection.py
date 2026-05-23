import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from src.apps.shared.schemas.enums import ChatEvent
from src.core.logger import logger

from .broker import EventBroker, event_broker
from .registry import ConnectionRegistry, connection_registry
from .types import Channel, ConnectionId, UserId

WebSocketHandler = Callable[
    [WebSocket, ConnectionId, EventBroker, dict[str, Any]],
    Awaitable[None],
]

WebSocketLifecycleHandler = Callable[
    [WebSocket, ConnectionId, EventBroker],
    Awaitable[None],
]


class WebSocketConnection:
    """
    Manages the full lifecycle of one WebSocket connection.

    On enter:
      - accepts the socket
      - registers the connection and joins it to its channels
      - spawns a background send loop that drains the connection's queue

    On exit:
      - cancels the send loop
      - removes the connection from the registry
      - closes the socket if still open

    The receive loop (run_until_disconnect) and the send loop run concurrently.
    Only the send loop calls websocket.send_json(); no other code should.
    """

    def __init__(
        self,
        *,
        websocket: WebSocket,
        user_id: UserId,
        channels: set[Channel],
        handlers: dict[ChatEvent, WebSocketHandler],
        registry: ConnectionRegistry = connection_registry,
        broker: EventBroker = event_broker,
        connect_handler: WebSocketLifecycleHandler | None = None,
        disconnect_handler: WebSocketLifecycleHandler | None = None,
    ) -> None:
        self._websocket = websocket
        self._user_id = user_id
        self._channels = channels
        self._handlers = handlers
        self._registry = registry
        self._broker = broker
        self._connect_handler = connect_handler
        self._disconnect_handler = disconnect_handler

        self.connection_id: ConnectionId | None = None
        self._send_task: asyncio.Task | None = None

    async def __aenter__(self) -> "WebSocketConnection":
        await self._websocket.accept()

        # TODO really need to pass user id?
        self.connection_id = self._registry.add(
            websocket=self._websocket, user_id=self._user_id
        )

        for channel in self._channels:
            self._registry.join_channel(self.connection_id, channel)

        self._send_task = asyncio.create_task(self._send_loop())

        if self._connect_handler is not None:
            await self._connect_handler(
                self._websocket, self.connection_id, self._broker
            )

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.connection_id is None:
            return

        try:
            if self._disconnect_handler is not None:
                await self._disconnect_handler(
                    self._websocket, self.connection_id, self._broker
                )
        finally:
            if self._send_task is not None:
                self._send_task.cancel()
                await asyncio.gather(self._send_task, return_exceptions=True)

            websocket = self._registry.remove(self.connection_id)

            if (
                websocket is not None
                and websocket.client_state == WebSocketState.CONNECTED
            ):
                try:
                    await websocket.close()
                except Exception:
                    pass

    async def run_until_disconnect(self) -> None:
        """Receive loop: reads incoming client messages and dispatches them to handlers."""

        try:
            async for text in self._websocket.iter_text():
                await self._process_text(text)
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.exception("[WebSocketConnection] receive loop failed")

    async def _send_loop(self) -> None:
        """Send loop: drains the connection's queue and writes events to the socket."""

        if self.connection_id is None:
            return

        try:
            while True:
                event = await self._registry.next_event(self.connection_id)
                await self._websocket.send_json(event)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("[WebSocketConnection] send loop failed")

    async def _process_text(self, text: str) -> None:
        assert self.connection_id is not None

        # if self.connection_id is None:
        #     return

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            await self._send_error("invalid json")
            return

        if not isinstance(payload, dict):
            await self._send_error("payload must be an object")
            return

        raw_event = payload.get("type")
        if not isinstance(raw_event, str):
            await self._send_error("missing event type")
            return

        try:
            event = ChatEvent(raw_event)
        except ValueError:
            await self._send_error(f"unknown event type: {raw_event!r}")
            return

        handler = self._handlers.get(event)
        if handler is None:
            await self._send_error(f"no handler for: {raw_event!r}")
            return

        await handler(
            self._websocket, self.connection_id, self._broker, payload
        )

    async def _send_error(self, detail: str) -> None:
        if self.connection_id is None:
            return

        await self._broker.send(
            self.connection_id,
            {"type": ChatEvent.error.value, "detail": detail},
        )
