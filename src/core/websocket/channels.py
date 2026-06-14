from uuid import UUID

from .types import Channel, UserId


def user_channel(user_id: UserId) -> Channel:
    return Channel(f"user:{user_id}")


def chat_channel(chat_id: UUID | str) -> Channel:
    return Channel(f"chat:{chat_id}")
