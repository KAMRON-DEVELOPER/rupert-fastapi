from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, Text
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from src.apps.users.models import UserModel


class BaseMessageModel(BaseModel):
    __abstract__ = True

    sender_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="users.id", ondelete="SET NULL"),
        index=True,
    )
    message: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    # Relationships
    @declared_attr
    def sender(cls) -> Mapped[UserModel | None]:
        return relationship(
            "UserModel", back_populates="chat_messages", passive_deletes=True
        )

    def __repr__(self) -> str:
        return f"<BaseMessageModel id={self.id}>"
