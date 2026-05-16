from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, TIMESTAMP
from sqlalchemy import UUID as PG_UUID
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class BaseMessageModel(BaseModel):
    __abstract__ = True

    sender_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey(column="users.id", ondelete="CASCADE")
    )
    message: Mapped[str] = mapped_column(Text)
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(item_type=String))
    video_urls: Mapped[list[str]] = mapped_column(ARRAY(item_type=String))
    scheduled_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))

    def __repr__(self):
        return "<BaseMessageModel>"
