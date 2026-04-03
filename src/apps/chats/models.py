from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.apps.shared.models import BaseModel, MessageBaseModel

if TYPE_CHECKING:
    from src.apps.users.models import UserModel


class ChatMessageModel(MessageBaseModel):
    __tablename__ = "chat_messages"

    chat_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="chats.id", ondelete="CASCADE"), index=True, nullable=False)

    # Relationships
    chat: Mapped["ChatModel"] = relationship(back_populates="messages", passive_deletes=True)
    sender: Mapped["UserModel"] = relationship(back_populates="chat_messages", passive_deletes=True)


class ChatParticipantModel(BaseModel):
    __tablename__ = "chat_participants"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="users.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="chats.id", ondelete="CASCADE"), primary_key=True)
    background_url: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="chat_participants")
    chat: Mapped["ChatModel"] = relationship(back_populates="participants")

    def __repr__(self):
        return "<ChatParticipantModel>"


class ChatModel(BaseModel):
    __tablename__ = "chats"

    last_message_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    # Relationships
    users: Mapped[list["UserModel"]] = relationship(secondary="chat_participants", back_populates="chats", viewonly=True)
    messages: Mapped[list["ChatMessageModel"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    participants: Mapped[list["ChatParticipantModel"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

    def __repr__(self):
        return "<ChatModel>"
