from collections import defaultdict
from uuid import uuid4

from fastapi import WebSocket

from .types import Channel, ConnectionId, UserId


class ConnectionRegistry:
    """
    Stores live WebSocket connections and their indexes.

    Role:
    - remember which sockets are alive
    - remember which user owns which sockets
    - remember which sockets are subscribed to which channels
    - cleanup everything quickly on disconnect

    It does not accept WebSockets.
    It does not send messages.
    It does not parse JSON.
    It does not know chat business logic.
    """

    def __init__(self) -> None:
        self._sockets: dict[ConnectionId, WebSocket] = {}
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

    def add_connection(
        self, *, websocket: WebSocket, user_id: UserId
    ) -> ConnectionId:
        connection_id = ConnectionId(uuid4().hex)

        self._sockets[connection_id] = websocket
        self._connection_users[connection_id] = user_id
        self._user_connections[user_id].add(connection_id)

        return connection_id

    def remove_connection(
        self, connection_id: ConnectionId
    ) -> WebSocket | None:
        websocket = self._sockets.pop(connection_id, None)

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

    def subscribe(self, connection_id: ConnectionId, channel: Channel) -> None:
        if connection_id not in self._sockets:
            return

        self._channel_connections[channel].add(connection_id)
        self._connection_channels[connection_id].add(channel)

    def unsubscribe(
        self, connection_id: ConnectionId, channel: Channel
    ) -> None:
        self._channel_connections[channel].discard(connection_id)
        self._connection_channels[connection_id].discard(channel)

        if not self._channel_connections[channel]:
            self._channel_connections.pop(channel, None)

        if not self._connection_channels[connection_id]:
            self._connection_channels.pop(connection_id, None)

    def get_socket(self, connection_id: ConnectionId) -> WebSocket | None:
        return self._sockets.get(connection_id)

    def get_channel_connections(self, channel: Channel) -> list[ConnectionId]:
        return list(self._channel_connections.get(channel, set()))

    def get_user_connections(self, user_id: UserId) -> list[ConnectionId]:
        return list(self._user_connections.get(user_id, set()))

    def get_connection_channels(
        self, connection_id: ConnectionId
    ) -> set[Channel]:
        return set(self._connection_channels.get(connection_id, set()))


connection_registry = ConnectionRegistry()
