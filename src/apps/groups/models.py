from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    literal_column,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from src.apps.shared.models import BaseMessageModel, BaseModel
from src.apps.shared.models.attachment import AttachmentModel
from src.apps.shared.schemas.enums import GroupMemberRole, GroupType

if TYPE_CHECKING:
    from src.apps.users.models import UserModel


class GroupMessageAttachmentLink(BaseModel):
    __tablename__ = "group_message_attachment_links"
    __table_args__ = (
        UniqueConstraint(
            "group_message_id",
            "attachment_id",
            name="uq_group_message_attachment",
        ),
        UniqueConstraint(
            "group_message_id",
            "position",
            name="uq_group_message_attachment_position",
        ),
    )

    group_message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="group_messages.id", ondelete="CASCADE"),
        index=True,
    )
    attachment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="attachments.id", ondelete="CASCADE"),
        index=True,
    )
    position: Mapped[int | None] = mapped_column(SmallInteger, default=None)

    # Relationships
    group_message: Mapped[GroupMessageModel] = relationship(
        back_populates="attachment_links"
    )
    attachment: Mapped[AttachmentModel] = relationship(
        back_populates="group_message_links"
    )

    def __repr__(self) -> str:
        return (
            f"<GroupMessageAttachmentLink "
            f"group_message_id={self.group_message_id} position={self.position}>"
        )


class GroupMessageModel(BaseMessageModel):
    __tablename__ = "group_messages"

    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="groups.id", ondelete="CASCADE"),
        index=True,
    )

    # Relationships
    group: Mapped[GroupModel] = relationship(
        back_populates="group_messages", passive_deletes=True
    )
    attachment_links: Mapped[list[GroupMessageAttachmentLink]] = relationship(
        back_populates="group_message",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="GroupMessageAttachmentLink.position",
    )


class GroupParticipantModel(BaseModel):
    __tablename__ = "group_participants"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="users.id", ondelete="CASCADE"),
        index=True,
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="groups.id", ondelete="CASCADE"),
        index=True,
    )
    background_url: Mapped[str | None] = mapped_column(Text)
    role: Mapped[GroupMemberRole] = mapped_column(
        Enum(GroupMemberRole, name="group_member_role"),
        default=GroupMemberRole.regular,
    )

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="group_participants")
    group: Mapped[GroupModel] = relationship(
        back_populates="group_participants"
    )

    def __repr__(self):
        return "<GroupParticipantModel>"


class GroupModel(BaseModel):
    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("name", name="uq_group_name"),)

    name: Mapped[str] = mapped_column(String(length=24))
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(column="users.id", ondelete="CASCADE"),
        index=True,
    )
    avatar_url: Mapped[str | None] = mapped_column(Text)
    background_url: Mapped[str | None] = mapped_column(Text)
    group_type: Mapped[GroupType] = mapped_column(
        Enum(GroupType, name="group_type"), default=GroupType.public
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    # Relationships
    users: Mapped[list[UserModel]] = relationship(
        secondary="group_participants", back_populates="groups", viewonly=True
    )
    group_messages: Mapped[list[GroupMessageModel]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    group_participants: Mapped[list[GroupParticipantModel]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Computed
    members_count: Mapped[int] = column_property(
        select(func.count(GroupParticipantModel.id))
        .where(GroupParticipantModel.group_id == literal_column("groups.id"))
        .correlate_except(GroupParticipantModel)
        .scalar_subquery()
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
