from typing import Any, Protocol

from .registry import ConnectionRegistry, connection_registry
from .types import UserId


class PresenceBackend(Protocol):
    async def is_online(self, user_id: UserId) -> bool: ...

    async def are_online(
        self, user_ids: list[UserId]
    ) -> dict[UserId, bool]: ...

    async def set_online(self, user_id: UserId) -> None: ...

    async def set_offline(self, user_id: UserId) -> None: ...


class LocalPresence:
    """Single-instance presence backed by ConnectionRegistry."""

    def __init__(
        self, registry: ConnectionRegistry = connection_registry
    ) -> None:
        self._registry = registry

    async def is_online(self, user_id: UserId) -> bool:
        return self._registry.user_has_connection(user_id)

    async def are_online(self, user_ids: list[UserId]) -> dict[UserId, bool]:
        return {
            uid: self._registry.user_has_connection(uid) for uid in user_ids
        }

    async def set_online(
        self,
        user_id: UserId,  # pyright: ignore[reportUnusedParameter]
    ) -> None: ...

    async def set_offline(
        self,
        user_id: UserId,  # pyright: ignore[reportUnusedParameter]
    ) -> None: ...


class RedisPresence:
    """Multi-instance presence backed by a Redis SET."""

    def __init__(self, redis: Any, key: str = "ws:online") -> None:
        self._redis = redis
        self._key = key

    async def is_online(self, user_id: UserId) -> bool:
        return bool(await self._redis.sismember(self._key, str(user_id)))

    async def are_online(self, user_ids: list[UserId]) -> dict[UserId, bool]:
        if not user_ids:
            return {}
        async with self._redis.pipeline() as pipe:
            for uid in user_ids:
                pipe.sismember(self._key, str(uid))
            results = await pipe.execute()
        return {uid: bool(r) for uid, r in zip(user_ids, results)}

    async def set_online(self, user_id: UserId) -> None:
        await self._redis.sadd(self._key, str(user_id))

    async def set_offline(self, user_id: UserId) -> None:
        await self._redis.srem(self._key, str(user_id))


presence: PresenceBackend = LocalPresence()
