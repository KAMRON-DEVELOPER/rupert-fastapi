from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import TIMESTAMP, Enum, ForeignKey, String, Text, UniqueConstraint, func, literal_column, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from src.apps.shared.models import BaseMessageModel, BaseModel
from src.apps.shared.schemas.enums import GroupMemberRole, GroupType

if TYPE_CHECKING:
    from src.apps.users.models import UserModel


class GroupMessageModel(BaseMessageModel):
    __tablename__ = "group_messages"

    group_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="groups.id", ondelete="CASCADE"), index=True)

    # Relationships
    group: Mapped[GroupModel] = relationship(back_populates="group_messages", passive_deletes=True)
    sender: Mapped[UserModel] = relationship(back_populates="group_messages", passive_deletes=True)


class GroupParticipantModel(BaseModel):
    __tablename__ = "group_participants"
    __table_args__ = (UniqueConstraint("user_id", "group_id", name="uq_user_group"),)

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="users.id", ondelete="CASCADE"), primary_key=True)
    group_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="groups.id", ondelete="CASCADE"), primary_key=True)
    background_url: Mapped[str | None] = mapped_column(Text)
    role: Mapped[GroupMemberRole] = mapped_column(Enum(GroupMemberRole, name="group_member_role"), default=GroupMemberRole.regular)

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="group_participants")
    group: Mapped[GroupModel] = relationship(back_populates="group_participants")

    def __repr__(self):
        return "<GroupParticipantModel>"


class GroupModel(BaseModel):
    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("name", name="uq_group_name"),)

    name: Mapped[str] = mapped_column(String(length=24))
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="users.id", ondelete="CASCADE"), index=True)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    background_url: Mapped[str | None] = mapped_column(Text)
    group_type: Mapped[GroupType] = mapped_column(Enum(GroupType, name="group_type"), default=GroupType.public)
    last_message_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Relationships
    users: Mapped[list[UserModel]] = relationship(secondary="group_participants", back_populates="groups", viewonly=True)
    group_messages: Mapped[list[GroupMessageModel]] = relationship(back_populates="group", passive_deletes=True)
    group_participants: Mapped[list[GroupParticipantModel]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Computed
    members_count: Mapped[int] = column_property(
        select(func.count(GroupParticipantModel.id)).where(GroupParticipantModel.group_id == literal_column("groups.id")).correlate_except(GroupParticipantModel).scalar_subquery()
    )
    administrators_count: Mapped[int] = column_property(
        select(func.count(GroupParticipantModel.id))
        .where(GroupParticipantModel.group_id == literal_column("groups.id"))
        .where(GroupParticipantModel.role == GroupMemberRole.administrator)
        .correlate_except(GroupParticipantModel)
        .scalar_subquery()
    )

    def __repr__(self):
        return "<GroupModel>"
