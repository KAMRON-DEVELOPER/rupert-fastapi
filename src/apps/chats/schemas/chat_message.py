from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.apps.shared.schemas.base import ResponseSchema


class ChatMessageResponse(ResponseSchema):
    id: UUID
    created_at: datetime
    updated_at: datetime
    sender_id: UUID | None
    message: str | None
    image_urls: list[str] = Field(default_factory=list)
    video_urls: list[str] = Field(default_factory=list)
    chat_id: UUID
    reply_id: UUID | None


class ChatListLastMessageResponse(ResponseSchema):
    id: UUID
    created_at: datetime
    updated_at: datetime
    sender_id: UUID | None
    message: str | None
    image_count: int
    video_count: int
    media_count: int
    reply_id: UUID | None
    preview: str
    is_mine: bool
    seen_by_other: bool | None
