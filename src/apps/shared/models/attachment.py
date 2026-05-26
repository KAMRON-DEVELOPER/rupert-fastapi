from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.apps.shared.schemas.enums import AttachmentStatus

from .base import BaseModel

if TYPE_CHECKING:
    from src.apps.chats.models import ChatMessageAttachmentLink
    from src.apps.feeds.models import FeedAttachmentLink
    from src.apps.groups.models import GroupMessageAttachmentLink


class AttachmentModel(BaseModel):
    __tablename__ = "attachments"

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    object_key: Mapped[str] = mapped_column(Text)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[AttachmentStatus] = mapped_column(
        Enum(AttachmentStatus, name="attachment_status"),
        default=AttachmentStatus.pending,
        index=True,
    )
    mime_type: Mapped[str] = mapped_column(String(255))
    label: Mapped[str] = mapped_column(String(64))
    group: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    chat_message_links: Mapped[list[ChatMessageAttachmentLink]] = relationship(
        back_populates="attachment", passive_deletes=True
    )
    group_message_links: Mapped[list[GroupMessageAttachmentLink]] = (
        relationship(back_populates="attachment", passive_deletes=True)
    )
    feed_links: Mapped[list[FeedAttachmentLink]] = relationship(
        back_populates="attachment", passive_deletes=True
    )

    def __repr__(self):
        size_mb = self.size_bytes / (1024 * 1024)
        return (
            f"<AttachmentModel object_key={self.object_key}, "
            f"group={self.group}, label={self.label}, size_mb={size_mb:.2f}>"
        )
