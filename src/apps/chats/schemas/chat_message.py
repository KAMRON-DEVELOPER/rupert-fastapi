from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from src.apps.shared.schemas.attachment import (
    AttachmentIdWithPositionRequest,
    AttachmentWithPositionResponse,
)
from src.apps.shared.schemas.base import RequestSchema, ResponseSchema


class CreateChatMessageRequest(RequestSchema):
    message: str | None = None
    chat_id: UUID | None = None
    reply_id: UUID | None = None
    participant_id: UUID | None = None
    attachments: list[AttachmentIdWithPositionRequest] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_payload(self):
        has_text = bool((self.message or "").strip())
        has_attachments = bool(self.attachments)

        if not has_text and not has_attachments:
            raise ValueError("message or attachments are required")

        if self.chat_id is None and self.participant_id is None:
            raise ValueError("chatId or participantId is required")

        positions = [item.position for item in self.attachments]
        if len(positions) != len(set(positions)):
            raise ValueError("attachment positions must be unique")

        return self


class UpdateChatMessageRequest(RequestSchema):
    message: str | None = None
    attachments: list[AttachmentIdWithPositionRequest] = Field(
        default_factory=list
    )


class ChatMessageResponse(ResponseSchema):
    id: UUID
    created_at: datetime
    updated_at: datetime
    sender_id: UUID | None
    message: str | None
    chat_id: UUID
    reply_id: UUID | None
    attachments: list[AttachmentWithPositionResponse] = Field(
        default_factory=list
    )


class ChatListLastMessageResponse(ChatMessageResponse):
    seen_by_recipient: bool | None
