import asyncio
import json
from typing import Any, ClassVar

from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from src.core.logger import logger

from .registry import ConnectionRegistry, connection_registry
from .types import Channel, ConnectionId


class RedisPubSubManager:
    """
    Optional Redis cluster bridge.

    One instance per FastAPI process, started in lifespan.
    Publishes events into Redis and mirrors incoming Redis messages
    back into local connection queues via the registry.

    All Redis channel names are prefixed with "ws:" so a single
    psubscribe("ws:*") captures the full event stream.
    """

    _instance: ClassVar[RedisPubSubManager | None] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> RedisPubSubManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        *,
        redis: Redis,
        registry: ConnectionRegistry = connection_registry,
        pattern: str = "ws:*",
    ) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.redis = redis
        self.registry = registry
        self.pattern = pattern

        self._pubsub: PubSub | None = None
        self._listener: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._listener is not None:
            return

        self._pubsub = self.redis.pubsub()
        await self._pubsub.psubscribe(self.pattern)
        self._listener = asyncio.create_task(self._listen())
        logger.info("[RedisPubSubManager] listener started")

    async def stop(self) -> None:
        if self._listener is not None:
            self._listener.cancel()
            await asyncio.gather(self._listener, return_exceptions=True)
            self._listener = None

        if self._pubsub is not None:
            await self._pubsub.aclose()
            self._pubsub = None

    async def publish(
        self,
        channel: Channel,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None:
        await self.redis.publish(
            f"{self.pattern}{channel}",
            json.dumps(
                {"channel": channel, "event": event, "exclude": exclude}
            ),
        )

    async def _listen(self) -> None:
        if self._pubsub is None:
            return

        try:
            async for message in self._pubsub.listen():
                if message.get("type") not in {"message", "pmessage"}:
                    continue

                await self._handle_message(message.get("data"))
        except asyncio.CancelledError:
            logger.info("[RedisPubSubManager] listener stopped")
        except Exception:
            logger.exception("[RedisPubSubManager] listener crashed")

    async def _handle_message(self, raw: Any) -> None:
        if raw is None:
            return

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("[RedisPubSubManager] invalid JSON: %r", raw)
            return

        channel = payload.get("channel")
        event = payload.get("event")
        exclude = payload.get("exclude")

        if not isinstance(channel, str) or not isinstance(event, dict):
            logger.warning("[RedisPubSubManager] invalid payload: %s", payload)
            return

        await self.registry.publish_local(
            Channel(channel),
            event,
            exclude=ConnectionId(exclude) if exclude else None,
        )
