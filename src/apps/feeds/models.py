from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import TIMESTAMP, Enum, Float, ForeignKey, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from src.apps.shared.models import BaseModel
from src.apps.shared.schemas.enums import CommentPolicy, FeedEngagementType, FeedVisibility
from src.apps.users.models import UserModel

if TYPE_CHECKING:
    from src.apps.shared.models import TagModel


class FeedCategoryModel(BaseModel):
    __tablename__ = "feed_categories"

    name: Mapped[str] = mapped_column(String(24), index=True, unique=True)

    # Relationships
    feeds: Mapped[list[FeedModel]] = relationship(back_populates="category")

    def __repr__(self):
        return "<CategoryModel>"


class FeedTagLink(BaseModel):
    __tablename__ = "feed_tag_links"

    feed_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="feeds.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="tags.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    feed: Mapped[FeedModel] = relationship(back_populates="tag_links", overlaps="feeds, tags")
    tag: Mapped[TagModel] = relationship(back_populates="feed_links", overlaps="feeds")

    def __repr__(self):
        return "<FeedTagLink>"


class FeedEngagementModel(BaseModel):
    __tablename__ = "feed_engagements"
    __table_args__ = (UniqueConstraint("user_id", "feed_id", "type", name="uq_user_feed_engagement"),)

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feed_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), index=True)
    type: Mapped[FeedEngagementType] = mapped_column(Enum(FeedEngagementType, name="feed_engagement_type"))

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="feed_engagements", passive_deletes=True)
    feed: Mapped[FeedModel] = relationship(back_populates="engagements", passive_deletes=True)

    def __repr__(self):
        return "<EngagementModel>"


class FeedModel(BaseModel):
    __tablename__ = "feeds"

    author_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    author_first_name: Mapped[str] = column_property(select(UserModel.first_name).where(UserModel.id == author_id).correlate_except(UserModel).scalar_subquery())
    author_last_name: Mapped[str] = column_property(select(UserModel.last_name).where(UserModel.id == author_id).correlate_except(UserModel).scalar_subquery())

    parent_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), index=True)
    quote_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("feed_categories.id", ondelete="CASCADE"), index=True)

    body: Mapped[str] = mapped_column(String(200))
    video_url: Mapped[str | None] = mapped_column(String(255))
    video_aspect_ratio: Mapped[float | None] = mapped_column(Float(precision=4))
    image_url: Mapped[str | None] = mapped_column(String(255))
    image_aspect_ratio: Mapped[float | None] = mapped_column(Float(precision=4))

    feed_visibility: Mapped[FeedVisibility] = mapped_column(Enum(FeedVisibility, name="feed_visibility"), default=FeedVisibility.public)
    comment_policy: Mapped[CommentPolicy] = mapped_column(Enum(CommentPolicy, name="comment_policy"), default=CommentPolicy.everyone)
    scheduled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Relationships
    author: Mapped[UserModel] = relationship(back_populates="feeds")
    parent: Mapped[FeedModel | None] = relationship(remote_side="FeedModel.id", back_populates="comments", foreign_keys=[parent_id])
    quote: Mapped[FeedModel | None] = relationship(remote_side="FeedModel.id", back_populates="quotes", foreign_keys=[quote_id])
    quotes: Mapped[list[FeedModel]] = relationship(back_populates="quote", foreign_keys=[quote_id], cascade="all, delete-orphan", passive_deletes=True)
    comments: Mapped[list[FeedModel]] = relationship(back_populates="parent", foreign_keys=[parent_id], cascade="all, delete-orphan", passive_deletes=True)
    category: Mapped[FeedCategoryModel | None] = relationship(back_populates="feeds")
    tag_links: Mapped[list[FeedTagLink]] = relationship(back_populates="feed", overlaps="feeds, tags", cascade="all, delete-orphan")
    tags: Mapped[list[TagModel]] = relationship(secondary="feed_tag_links", back_populates="feeds", viewonly=True)
    engagements: Mapped[list[FeedEngagementModel]] = relationship(back_populates="feed", cascade="all, delete-orphan")

    def __repr__(self):
        return "<FeedModel>"
