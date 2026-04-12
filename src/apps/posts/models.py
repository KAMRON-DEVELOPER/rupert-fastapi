from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import TIMESTAMP, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.apps.shared.enums import PostEngagementType, PostStatus
from src.apps.shared.models import BaseModel

if TYPE_CHECKING:
    from src.apps.shared.models import TagModel
    from src.apps.users.models import UserModel


class PostTagLink(BaseModel):
    __tablename__ = "post_tag_links"

    post_id: Mapped[UUID] = mapped_column(ForeignKey(column="posts.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey(column="tags.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    post: Mapped["PostModel"] = relationship(back_populates="tag_links", overlaps="posts,tags")
    tag: Mapped["TagModel"] = relationship(back_populates="post_links", overlaps="posts,tag_links")

    def __repr__(self):
        return "<PostTagLink>"


class PostEngagementModel(BaseModel):
    __tablename__ = "post_engagements"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post_engagement"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[PostEngagementType] = mapped_column(Enum(PostEngagementType, name="post_engagement_type"), nullable=False)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="post_engagements", passive_deletes=True)
    post: Mapped["PostModel"] = relationship(back_populates="engagements", passive_deletes=True)

    def __repr__(self):
        return "<PostEngagementModel>"


class PostCommentModel(BaseModel):
    __tablename__ = "post_comments"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("post_comments.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="post_comments")
    post: Mapped[PostModel] = relationship(back_populates="comments")
    parent: Mapped[PostCommentModel | None] = relationship(remote_side="PostCommentModel.id", back_populates="replies")
    replies: Mapped[list[PostCommentModel]] = relationship(back_populates="parent", cascade="all, delete-orphan")

    def __repr__(self):
        return "<PostCommentModel>"


class PostModel(BaseModel):
    __tablename__ = "posts"

    author_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus, name="post_status"), default=PostStatus.draft)
    scheduled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Relationships
    author: Mapped["UserModel"] = relationship(back_populates="posts")
    tag_links: Mapped[list["PostTagLink"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    tags: Mapped[list["TagModel"]] = relationship(secondary="post_tag_links", back_populates="posts", viewonly=True)
    engagements: Mapped[list["PostEngagementModel"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["PostCommentModel"]] = relationship(back_populates="post", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return "<PostModel>"
