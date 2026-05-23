from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.apps.shared.schemas.enums import AttachmentKind, AttachmentStatus

from .base import BaseModel

if TYPE_CHECKING:
    from src.apps.chats.models import ChatMessageAttachmentLink


class AttachmentModel(BaseModel):
    __tablename__ = "attachments"

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    object_key: Mapped[str] = mapped_column(Text, unique=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    kind: Mapped[AttachmentKind] = mapped_column(
        Enum(AttachmentKind, name="attachment_kind"), index=True
    )
    status: Mapped[AttachmentStatus] = mapped_column(
        Enum(AttachmentStatus, name="attachment_status"),
        default=AttachmentStatus.pending,
        index=True,
    )
    content_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    chat_message_links: Mapped[list["ChatMessageAttachmentLink"]] = (
        relationship(back_populates="attachment", passive_deletes=True)
    )

    def __repr__(self):
        size_mb = self.size_bytes / (1024 * 1024)
        return (
            f"<AttachmentModel object_key={self.object_key}, "
            f"kind={self.kind.value}, size_mb={size_mb:.2f}>"
        )
