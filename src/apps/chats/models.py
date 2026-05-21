from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.apps.shared.models import BaseMessageModel, BaseModel

if TYPE_CHECKING:
    from src.apps.users.models import UserModel


class ChatMessageModel(BaseMessageModel):
    __tablename__ = "chat_messages"

    chat_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="chats.id", ondelete="CASCADE"),
        index=True,
    )
    reply_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="chat_messages.id", ondelete="SET NULL"),
        index=True,
    )

    # Relationships
    sender: Mapped[UserModel] = relationship(
        back_populates="chat_messages", passive_deletes=True
    )
    chat: Mapped[ChatModel] = relationship(
        back_populates="messages", passive_deletes=True
    )
    reply: Mapped[ChatMessageModel | None] = relationship(
        remote_side="ChatMessageModel.id",
        foreign_keys=[reply_id],
    )


class ChatParticipantModel(BaseModel):
    __tablename__ = "chat_participants"
    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", name="uq_chat_participant"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="users.id", ondelete="CASCADE"),
        index=True,
    )
    chat_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="chats.id", ondelete="CASCADE"),
        index=True,
    )
    background_url: Mapped[str | None] = mapped_column(Text)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    last_online_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    # this participant has read messages in this chat up to this timestamp.
    last_seen_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    cleared_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="chat_participants")
    chat: Mapped[ChatModel] = relationship(back_populates="participants")

    def __repr__(self):
        return f"<ChatParticipantModel user_id={self.user_id} chat_id={self.chat_id}>"


class ChatModel(BaseModel):
    __tablename__ = "chats"

    # Relationships
    users: Mapped[list[UserModel]] = relationship(
        secondary="chat_participants", back_populates="chats", viewonly=True
    )
    participants: Mapped[list[ChatParticipantModel]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    messages: Mapped[list[ChatMessageModel]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return "<ChatModel>"
