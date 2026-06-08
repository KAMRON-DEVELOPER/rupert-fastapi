from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from pydantic import Field, model_validator

from src.apps.chats.schemas.chat_message import ChatMessageUpdateRequest
from src.apps.chats.schemas.chat_participant import ChatSettingsRequest
from src.apps.shared.schemas.base import RequestSchema

TRequest = TypeVar("TRequest", bound=RequestSchema)
Action = Callable[[], Awaitable[None]]


class ChatRoomActionRequest(RequestSchema):
    chat_id: UUID


class MessageActionRequest(ChatRoomActionRequest):
    message_id: UUID


class ReadChatRequest(ChatRoomActionRequest):
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScopedChatActionRequest(ChatRoomActionRequest):
    for_participant: bool = False


class UpdateChatSettingsActionRequest(ChatSettingsRequest):
    chat_id: UUID

    @model_validator(mode="after")
    def validate_values(self):
        if (
            self.is_pinned is None
            and self.is_muted is None
            and self.is_archived is None
        ):
            raise ValueError("at least one chat setting is required")
        return self


class UpdateMessageActionRequest(ChatMessageUpdateRequest):
    chat_id: UUID
    message_id: UUID
