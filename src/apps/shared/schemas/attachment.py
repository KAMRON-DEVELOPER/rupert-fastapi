from uuid import UUID

from pydantic import Field, computed_field

from .base import RequestSchema, ResponseSchema
from .enums import AttachmentKind, AttachmentStatus


from src.core.settings import get_settings

settings = get_settings()


def build_attachment_url(object_key: str) -> str:
    s = settings.s3
    scheme = "http" if settings.debug else "https"
    return f"{scheme}://{s.endpoint}/{s.bucket_name}/{object_key}"


class ChatMessageAttachmentRequest(RequestSchema):
    id: UUID
    position: int = Field(ge=0)


class AttachmentResponse(ResponseSchema):
    id: UUID
    object_key: str
    original_filename: str | None
    kind: AttachmentKind
    status: AttachmentStatus
    content_type: str
    size_bytes: int
    meta: dict = Field(default_factory=dict)

    @computed_field
    @property
    def url(self) -> str:
        return build_attachment_url(self.object_key)


class ChatMessageAttachmentResponse(AttachmentResponse):
    position: int
