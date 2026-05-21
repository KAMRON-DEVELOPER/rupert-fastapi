from uuid import UUID

from pydantic import Field

from src.apps.chats.schemas.chat_message import (
    ChatListLastMessageResponse,
)
from src.apps.chats.schemas.chat_participant import ChatListUserResponse
from src.apps.shared.schemas.base import RequestSchema, ResponseSchema


class CreateChatSchema(RequestSchema):
    participant_id: UUID


class ChatListItemResponse(ResponseSchema):
    id: UUID
    user: ChatListUserResponse
    is_pinned: bool
    is_muted: bool
    is_archived: bool
    last_message: ChatListLastMessageResponse | None = None
    unread_count: int = Field(ge=0)
