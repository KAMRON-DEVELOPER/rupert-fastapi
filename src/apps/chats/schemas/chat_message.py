from uuid import UUID

from pydantic import Field, model_validator

from src.apps.shared.schemas import BaseModelResponse
from src.apps.shared.schemas.attachment import (
    AttachmentIdWithPositionRequest,
    AttachmentWithPositionResponse,
)
from src.apps.shared.schemas.base import RequestSchema


class ChatMessageCreateRequest(RequestSchema):
    message: str | None = None
    chat_id: UUID
    reply_id: UUID | None = None
    attachments: list[AttachmentIdWithPositionRequest] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_payload(self):
        has_text = bool((self.message or "").strip())
        has_attachments = bool(self.attachments)

        if not has_text and not has_attachments:
            raise ValueError("message or attachments are required")

        positions = [item.position for item in self.attachments]
        if len(positions) != len(set(positions)):
            raise ValueError("attachment positions must be unique")

        return self


class ChatMessageUpdateRequest(RequestSchema):
    message: str | None = None
    attachments: list[AttachmentIdWithPositionRequest] | None = None

    @model_validator(mode="after")
    def validate_payload(self):
        has_text = self.message is not None
        has_attachments = self.attachments is not None

        if not has_text and not has_attachments:
            raise ValueError("message or attachments are required")

        positions = [item.position for item in self.attachments or []]
        if len(positions) != len(set(positions)):
            raise ValueError("attachment positions must be unique")

        return self


class ChatMessageResponse(BaseModelResponse):
    sender_id: UUID | None
    message: str | None
    chat_id: UUID
    reply_id: UUID | None
    attachments: list[AttachmentWithPositionResponse] = Field(
        default_factory=list
    )


class ChatListLastMessageResponse(ChatMessageResponse):
    seen_by_recipient: bool | None
