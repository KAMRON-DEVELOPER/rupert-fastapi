import json
from datetime import UTC, datetime
from inspect import isawaitable
from time import time
from typing import Optional
from uuid import UUID, uuid4

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.client import PubSub

from src.apps.chats.schemas import ChatMessageSchema, ChatResponseSchema, ChatSchema, ParticipantSchema
from src.utils.logger import logger
from src.utils.settings import get_settings

settings = get_settings()


def create_redis():
    """Create redis client"""

    if settings.redis.url:
        pool = ConnectionPool.from_url(settings.redis.url)
        return Redis.from_pool(pool)
    if settings.redis.params:
        return Redis(
            host=settings.redis.params.host,
            port=settings.redis.params.port,
            db=settings.redis.params.db,
            username=settings.redis.params.username,
            password=settings.redis.params.password,
            decode_responses=True,
            auto_close_connection_pool=True,
        )

    raise Exception("Redis url and params not set")


class RedisPubSubManager:
    def __init__(self, client: Redis):
        self.client = client
        self.active_subscriptions: dict[str, PubSub] = {}

    async def publish(self, topic: str, data: dict):
        await self.client.publish(channel=topic, message=json.dumps(data))

    async def subscribe(self, topic: str) -> PubSub:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(topic)
        self.active_subscriptions[topic] = pubsub
        return pubsub

    async def unsubscribe(self, topic: str):
        if pubsub := self.active_subscriptions.get(topic):
            try:
                await pubsub.unsubscribe(topic)
                await pubsub.close()
            finally:
                self.active_subscriptions.pop(topic, None)


class ChatCacheManager:
    def __init__(self, client: Redis):
        self.client = client

    async def create_chat(self, user_id: str, participant_id: str, chat_id: str, mapping: dict):
        last_message: dict = mapping.pop("last_message")
        now_timestamp = datetime.now(UTC).timestamp()
        async with self.client.pipeline() as pipe:
            pipe.zadd(name=f"users:{user_id}:chats", mapping={chat_id: now_timestamp})
            pipe.zadd(name=f"users:{participant_id}:chats", mapping={chat_id: now_timestamp})
            pipe.hset(name=f"chats:{chat_id}:meta", mapping=mapping)
            pipe.hset(name=f"chats:{chat_id}:last_message", mapping=last_message)
            pipe.sadd(f"chats:{chat_id}:participants", user_id, participant_id)
            await pipe.execute()

    async def delete_chat(self, participants: list[str], chat_id: str):
        async with self.client.pipeline() as pipe:
            for pid in participants:
                pipe.zrem(f"users:{pid}:chats", chat_id)
                pipe.delete(f"chats:{chat_id}:meta")
                pipe.delete(f"chats:{chat_id}:last_message")
            pipe.srem(f"chats:{chat_id}:participants", *participants)
            await pipe.execute()

    async def get_chats(self, user_id: str, start: int = 0, end: int = 20) -> ChatResponseSchema:
        chat_ids: list[str] = await self.client.zrevrange(name=f"users:{user_id}:chats", start=start, end=end)
        if not chat_ids:
            return ChatResponseSchema(chats=[], end=0)

        async with self.client.pipeline() as pipe:
            for chat_id in chat_ids:
                pipe.hgetall(f"chats:{chat_id}:meta")  # index 0, 3, 6...
                pipe.hgetall(f"chats:{chat_id}:last_message")  # index 1, 4, 7...
                pipe.smembers(f"chats:{chat_id}:participants")  # index 2, 5, 8...
            results = await pipe.execute()

        chats: list[dict] = results[::3]  # Every 3rd element starting at 0
        last_messages: list[dict] = results[1::3]  # Every 3rd element starting at 1
        participant_sets: list[set[str]] = results[2::3]  # Every 3rd element starting at 2

        participant_ids: list[str] = []
        for participant_set in participant_sets:
            participant_set.discard(user_id)
            pid: Optional[str] = next(iter(participant_set), None)
            if not pid:
                continue
            participant_ids.append(pid)

        async with self.client.pipeline() as pipe:
            for pid in participant_ids:
                pipe.hgetall(f"users:{pid}:profile")
            for pid in participant_ids:
                pipe.sismember("chats:online", pid)
            piped_results = await pipe.execute()

        profiles: list[dict] = piped_results[: len(participant_ids)]
        statuses: list[bool] = piped_results[len(participant_ids) :]

        chat_list = []
        for chat_meta, last_msg, pid, profile, is_online in zip(chats, last_messages, participant_ids, profiles, statuses):
            if not pid or not profile:
                continue

            chat = ChatSchema(
                id=UUID(chat_meta["id"]) if "id" in chat_meta else uuid4(),
                participant=ParticipantSchema(
                    id=UUID(hex=pid),
                    name=profile.get("name", ""),
                    username=profile.get("username", ""),
                    avatar_url=profile.get("avatar_url"),
                    last_seen_at=datetime.fromtimestamp(int(profile.get("last_seen_at", 0))) if "last_seen_at" in profile else None,
                    is_online=is_online,
                ),
                last_activity_at=datetime.fromtimestamp(float(chat_meta.get("last_activity_at", time()))),
                last_message=ChatMessageSchema(
                    id=UUID(hex=last_msg.get("id", "")),
                    sender_id=UUID(hex=last_msg.get("sender_id", "")),
                    chat_id=UUID(hex=last_msg.get("chat_id", "")),
                    message=last_msg.get("message", ""),
                    created_at=datetime.fromtimestamp(float(last_msg.get("created_at", time()))),
                ),
            )
            chat_list.append(chat)

        return ChatResponseSchema(chats=chat_list, end=len(chat_ids) - 1)

    async def is_user_chat_owner(self, user_id: str, chat_id: str) -> bool:
        score: Optional[float] = await self.client.zscore(name=f"users:{user_id}:chats", value=chat_id)
        logger.warning(f"user_id: {user_id}")
        logger.warning(f"chat_id: {chat_id}")
        logger.warning(f"score: {score}")
        return False if score is None else True

    async def is_online(self, participant_id: str) -> bool:
        is_member = self.client.sismember(name="chats:online", value=participant_id)
        return bool(await is_member) if isawaitable(is_member) else bool(is_member)

    """ ****************************************** EVENTS ****************************************** """

    async def add_user_to_chats(self, user_id: str) -> tuple[set[str], set[str]]:
        chat_ids: list[str] = await self.client.zrevrange(name=f"users:{user_id}:chats", start=0, end=-1)

        async with self.client.pipeline() as pipe:
            pipe.sadd("chats:online", user_id)
            for chat_id in chat_ids:
                pipe.sinter([f"chats:{chat_id}:participants", "chats:online"])
            results = await pipe.execute()

        online_participants: set[str] = set()
        chat_ids_with_online: set[str] = set()
        online_users_per_chat_results: list[set[str]] = results[1:]

        for chat_id, online_in_chat in zip(chat_ids, online_users_per_chat_results):
            other_online_users = {pid for pid in online_in_chat if pid != user_id}
            if other_online_users:
                chat_ids_with_online.add(chat_id)
                online_participants.update(other_online_users)

        return chat_ids_with_online, online_participants

    async def remove_user_from_chats(self, user_id: str) -> tuple[set[str], set[str]]:
        chat_ids: list[str] = await self.client.zrevrange(name=f"users:{user_id}:chats", start=0, end=-1)

        async with self.client.pipeline() as pipe:
            pipe.srem("chats:online", user_id)
            pipe.hset(f"users:{user_id}:profile", key="last_seen_at", value=str(datetime.now(UTC).timestamp()))
            for chat_id in chat_ids:
                pipe.sinter([f"chats:{chat_id}:participants", "chats:online"])
            results = await pipe.execute()

        online_participants: set[str] = set()
        chat_ids_with_online: set[str] = set()
        online_users_per_chat_results: list[set[str]] = results[2:]

        for chat_id, online_in_chat in zip(chat_ids, online_users_per_chat_results):
            other_online_users = {pid for pid in online_in_chat if pid != user_id}
            if other_online_users:
                chat_ids_with_online.add(chat_id)
                online_participants.update(other_online_users)

        return chat_ids_with_online, online_participants

    async def get_chat_participants(self, chat_id: str, user_id: str | None = None, online: bool = False) -> set[str]:
        if online:
            is_intersected = self.client.sinter([f"chats:{chat_id}:participants", "chats:online"])
            participants = set(await is_intersected) if isawaitable(is_intersected) else set(is_intersected)
            if user_id:
                participants.discard(user_id)
            return participants
        else:
            is_member = self.client.smembers(f"chats:{chat_id}:participants")
            return await is_member if isawaitable(is_member) else is_member


class CacheManager:
    def __init__(self, client: Redis):
        self.client = client
