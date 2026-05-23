from typing import Any, Protocol

from .registry import ConnectionRegistry, connection_registry
from .types import Channel, ConnectionId


class PubSubBridge(Protocol):
    async def publish(
        self,
        channel: Channel,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None: ...


class EventBroker:
    """
    The only object handlers should interact with.

    Single-instance mode (no Redis):
        broker = EventBroker(registry=registry)
        publish() writes directly into local queues.

    Cluster mode (with Redis):
        broker = EventBroker(registry=registry, pubsub=redis_pubsub_manager)
        publish() sends to Redis; the global listener echoes it back
        into local queues on every server node.
    """

    def __init__(
        self,
        *,
        registry: ConnectionRegistry = connection_registry,
        pubsub: PubSubBridge | None = None,
    ) -> None:
        self._registry = registry
        self._pubsub = pubsub

    async def send(
        self, connection_id: ConnectionId, event: dict[str, Any]
    ) -> None:
        """Deliver an event to a single connection."""

        await self._registry.enqueue(connection_id, event)

    async def publish(
        self,
        channel: Channel,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None:
        """Broadcast an event to every connection in the channel."""

        if self._pubsub is not None:
            await self._pubsub.publish(channel, event, exclude=exclude)
        else:
            await self._registry.publish_local(channel, event, exclude=exclude)


event_broker = EventBroker()
