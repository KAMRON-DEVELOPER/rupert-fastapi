import json
from typing import Any

from redis.asyncio import Redis

from src.core.websocket.registry import ConnectionRegistry

from ..types import Channel, ConnectionId, UserId
from .local import LocalWebSocketTransport


class RedisWebSocketTransport:
    def __init__(self, *, registry: ConnectionRegistry, redis: Redis) -> None:
        self.registry = registry
        self.redis = redis
        self.local = LocalWebSocketTransport(registry)

    async def send(self, connection_id: ConnectionId, event: dict[str, Any]):
        # Direct send is always local.
        await self.local.send(connection_id, event)

    async def publish(
        self,
        channel: Channel,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ):
        # Cross-instance publish.
        await self.redis.publish(
            channel,
            json.dumps(
                {
                    "channel": channel,
                    "event": event,
                    "exclude": str(exclude) if exclude else None,
                }
            ),
        )

    async def publish_to_user(
        self,
        user_id: UserId,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ):
        await self.redis.publish(
            f"user:{user_id}",
            json.dumps(
                {
                    "channel": f"user:{user_id}",
                    "event": event,
                    "exclude": str(exclude) if exclude else None,
                }
            ),
        )
