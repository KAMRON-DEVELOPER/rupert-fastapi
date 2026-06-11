import asyncio
from collections import defaultdict
from typing import Any, ClassVar
from uuid import uuid4

from fastapi import WebSocket

from .types import Channel, ConnectionId, UserId


class ConnectionRegistry:
    """
    Singleton in-memory store for active connections.

    Owns three indexes:
        connection_id → WebSocket + outbound Queue
        channel       → set[ConnectionId]
        connection_id → set[Channel]

    The only place websocket.send_json() is ever called is WebSocketConnection._send_loop.
    Everything here only enqueues.
    """

    _instance: ClassVar[ConnectionRegistry | None] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> ConnectionRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *, queue_maxsize: int = 100) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.queue_maxsize = queue_maxsize

        self._sockets: dict[ConnectionId, WebSocket] = {}
        self._queues: dict[ConnectionId, asyncio.Queue[dict[str, Any]]] = {}

        self._connection_users: dict[ConnectionId, UserId] = {}
        self._user_connections: dict[UserId, set[ConnectionId]] = defaultdict(
            set
        )

        self._channel_connections: dict[Channel, set[ConnectionId]] = (
            defaultdict(set)
        )
        self._connection_channels: dict[ConnectionId, set[Channel]] = (
            defaultdict(set)
        )

    def add(self, *, websocket: WebSocket, user_id: UserId) -> ConnectionId:
        connection_id = ConnectionId(uuid4().hex)

        self._sockets[connection_id] = websocket
        self._queues[connection_id] = asyncio.Queue(maxsize=self.queue_maxsize)

        self._connection_users[connection_id] = user_id
        self._user_connections[user_id].add(connection_id)

        return connection_id

    def remove(self, connection_id: ConnectionId) -> WebSocket | None:
        websocket = self._sockets.pop(connection_id, None)
        self._queues.pop(connection_id, None)

        user_id = self._connection_users.pop(connection_id, None)
        if user_id is not None:
            self._user_connections[user_id].discard(connection_id)
            if not self._user_connections[user_id]:
                self._user_connections.pop(user_id, None)

        channels = self._connection_channels.pop(connection_id, set())
        for channel in channels:
            self._channel_connections[channel].discard(connection_id)
            if not self._channel_connections[channel]:
                self._channel_connections.pop(channel, None)

        return websocket

    def join_channel(
        self, connection_id: ConnectionId, channel: Channel
    ) -> None:
        if connection_id not in self._sockets:
            return

        self._channel_connections[channel].add(connection_id)
        self._connection_channels[connection_id].add(channel)

    def leave_channel(
        self, connection_id: ConnectionId, channel: Channel
    ) -> None:
        self._channel_connections[channel].discard(connection_id)
        self._connection_channels[connection_id].discard(channel)

        if not self._channel_connections[channel]:
            self._channel_connections.pop(channel, None)
        if not self._connection_channels[connection_id]:
            self._connection_channels.pop(connection_id, None)

    def user_has_channel_connection(
        self,
        user_id: UserId,
        channel: Channel,
        *,
        exclude: ConnectionId | None = None,
    ) -> bool:
        return any(
            connection_id != exclude
            and channel in self._connection_channels.get(connection_id, set())
            for connection_id in self._user_connections.get(user_id, set())
        )

    def user_has_connection(
        self, user_id: UserId, *, exclude: ConnectionId | None = None
    ) -> bool:
        return any(
            connection_id != exclude
            for connection_id in self._user_connections.get(user_id, set())
        )

    async def next_event(self, connection_id: ConnectionId) -> dict[str, Any]:
        """Awaited by WebSocketConnection._send_loop to drain a connection's queue."""
        queue = self._queues.get(connection_id)
        if queue is None:
            # If the queue was removed (e.g., due to QueueFull),
            # raise a CancelledError to kill the _send_loop gracefully.
            raise asyncio.CancelledError("Connection queue removed")

        return await queue.get()

    async def enqueue(
        self, connection_id: ConnectionId, event: dict[str, Any]
    ) -> None:
        queue = self._queues.get(connection_id)
        if queue is None:
            return

        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            # A connection whose queue is full is too slow to keep up.
            # Drop it rather than blocking the broadcast.

            # Remove from registry so we stop broadcasting to them
            websocket = self.remove(connection_id)

            # Forcefully sever the actual network connection
            if websocket is not None:
                # Run in a background task so we don't block the event broker!
                # Code 1008 (Policy Violation) is standard for rate/speed limits.
                asyncio.create_task(self._close_socket(websocket))

    async def _close_socket(self, websocket: WebSocket) -> None:
        """Helper to safely close sockets without crashing the broker."""
        try:
            await websocket.close(code=1008, reason="Client too slow")
        except Exception:
            pass  # The socket might have closed naturally in the last millisecond

    async def publish_local(
        self,
        channel: Channel,
        event: dict[str, Any],
        *,
        exclude: ConnectionId | None = None,
    ) -> None:
        """Enqueue an event for every connection currently in the channel."""
        for cid in list(self._channel_connections.get(channel, set())):
            if cid != exclude:
                await self.enqueue(cid, event)


connection_registry = ConnectionRegistry()
