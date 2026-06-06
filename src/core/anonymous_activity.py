from datetime import UTC, date, datetime, timedelta
from inspect import isawaitable
from typing import Protocol

from redis.asyncio import Redis


class AnonymousActivityBackend(Protocol):
    async def record(self, anonymous_id: str, activity_date: date) -> None: ...
    async def count(self, activity_date: date) -> int: ...


class LocalAnonymousActivityBackend:
    """Single-process in-memory backend."""

    def __init__(self):
        self._data: dict[str, set[str]] = {}

    async def record(self, anonymous_id: str, activity_date: date) -> None:
        key = activity_date.isoformat()
        if key not in self._data:
            self._data[key] = set()
        self._data[key].add(anonymous_id)

    async def count(self, activity_date: date) -> int:
        return len(self._data.get(activity_date.isoformat(), set()))


class RedisAnonymousActivityBackend:
    """Multi-process Redis backend."""

    def __init__(self, redis: Redis, key_prefix: str = "anonymous:active"):
        self._redis = redis
        self._prefix = key_prefix

    def _key(self, activity_date: date) -> str:
        return f"{self._prefix}:{activity_date.isoformat()}"

    async def record(self, anonymous_id: str, activity_date: date) -> None:
        key = self._key(activity_date)
        sadd = self._redis.sadd(key, anonymous_id)
        if isawaitable(sadd):
            await sadd
        await self._redis.expire(key, 31 * 86400)

    async def count(self, activity_date: date) -> int:
        scard = self._redis.scard(self._key(activity_date))
        if isawaitable(scard):
            return await scard
        return scard


# swap backend here
_backend: AnonymousActivityBackend = LocalAnonymousActivityBackend()


def configure_anonymous_activity(redis: Redis) -> None:
    """Call this in your app lifespan to switch to Redis."""
    global _backend
    _backend = RedisAnonymousActivityBackend(redis)


async def record_anonymous_activity(anonymous_id: str) -> None:
    today = datetime.now(UTC).date()
    await _backend.record(anonymous_id, today)


async def get_anonymous_dau_counts(
    start_date: date, days: int = 30
) -> dict[date, int]:
    result: dict[date, int] = {}
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        result[day] = await _backend.count(day)
    return result
