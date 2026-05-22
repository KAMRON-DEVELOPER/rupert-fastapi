import asyncio
from typing import Any

from src.core.logger import logger
from src.core.websocket.registry import ConnectionRegistry, connection_registry

from ..types import Channel, ConnectionId, UserId


class LocalWebSocketTransport:
    """
    Sends events to live WebSocket connections.

    Role:
    - send to one connection
    - publish to a channel
    - publish to all devices of one user

    It does not own connection lifecycle.
    It does not parse incoming messages.
    It does not know chat logic.
    """

    def __init__(self, registry: ConnectionRegistry) -> None:
        self.registry = registry

    async def send(
        self, connection_id: ConnectionId, event: dict[str, Any]
    ) -> None:
        websocket = self.registry.get_socket(connection_id)
        if websocket is None:
            return

        try:
            await websocket.send_json(event)
        except Exception as exc:
            logger.warning("[WebSocketTransport] direct send failed: %s", exc)

            websocket = self.registry.remove_connection(connection_id)
            if websocket is not None:
                try:
                    await websocket.close()
                except Exception:
                    pass

    async def publish(
        self,
        channel: Channel,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None:
        connection_ids = self.registry.get_channel_connections(channel)

        futures = (
            self.send(connection_id, event)
            for connection_id in connection_ids
            if connection_id != exclude
        )
        await asyncio.gather(*futures, return_exceptions=True)

    async def publish_to_user(
        self,
        user_id: UserId,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None:
        connection_ids = self.registry.get_user_connections(user_id)

        futures = (
            self.send(connection_id, event)
            for connection_id in connection_ids
            if connection_id != exclude
        )
        await asyncio.gather(*futures, return_exceptions=True)


websocket_transport = LocalWebSocketTransport(connection_registry)
