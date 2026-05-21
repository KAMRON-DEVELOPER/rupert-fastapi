from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, TIMESTAMP, ForeignKey, String, Text
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class BaseMessageModel(BaseModel):
    __abstract__ = True

    sender_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="users.id", ondelete="SET NULL"),
        index=True,
    )
    message: Mapped[str | None] = mapped_column(Text)
    image_urls: Mapped[list[str]] = mapped_column(
        ARRAY(item_type=String), default=list, server_default="{}"
    )
    video_urls: Mapped[list[str]] = mapped_column(
        ARRAY(item_type=String), default=list, server_default="{}"
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    def __repr__(self):
        return "<BaseMessageModel>"
