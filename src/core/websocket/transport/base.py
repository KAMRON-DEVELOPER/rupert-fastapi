from typing import Any, Protocol

from ..types import Channel, ConnectionId, UserId


class WebSocketTransport(Protocol):
    async def send(
        self, connection_id: ConnectionId, event: dict[str, Any]
    ) -> None: ...

    async def publish(
        self,
        channel: Channel,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None: ...

    async def publish_to_user(
        self,
        user_id: UserId,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None: ...
