from uuid import UUID

from pydantic import Field, computed_field

from src.core.settings import get_settings

from .base import RequestSchema, ResponseSchema
from .enums import AttachmentStatus

settings = get_settings()


def build_attachment_url(object_key: str) -> str:
    s = settings.s3
    scheme = "http" if settings.debug else "https"
    return f"{scheme}://{s.endpoint}/{s.bucket_name}/{object_key}"


class AttachmentIdWithPositionRequest(RequestSchema):
    attachment_id: UUID
    position: int | None = Field(default=None, ge=0)


class AttachmentResponse(ResponseSchema):
    id: UUID
    object_key: str
    original_filename: str | None
    status: AttachmentStatus
    mime_type: str
    label: str
    group: str
    size_bytes: int
    meta: dict = Field(default_factory=dict)

    @computed_field
    @property
    def url(self) -> str:
        return build_attachment_url(self.object_key)


class AttachmentWithPositionResponse(AttachmentResponse):
    position: int | None = Field(default=None, ge=0)


class AttachmentWithPositionableResponse(AttachmentResponse):
    is_positionable: bool


class UploadAttachmentsResponse(ResponseSchema):
    attachments: list[AttachmentWithPositionableResponse]
    failed: list[str]
