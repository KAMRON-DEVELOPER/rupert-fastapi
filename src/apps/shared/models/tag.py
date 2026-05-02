from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from src.apps.feeds.models import FeedModel, FeedTagLink
    from src.apps.posts.models import PostModel, PostTagLink


class TagModel(BaseModel):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(length=24), unique=True, nullable=False)

    # Relationships
    post_links: Mapped[list[PostTagLink]] = relationship(back_populates="tag", cascade="all, delete-orphan")
    posts: Mapped[list[PostModel]] = relationship(secondary="post_tag_links", back_populates="tags", viewonly=True)

    feed_links: Mapped[list[FeedTagLink]] = relationship(back_populates="tag", cascade="all, delete-orphan")
    feeds: Mapped[list[FeedModel]] = relationship(secondary="feed_tag_links", back_populates="tags", viewonly=True)

    def __repr__(self):
        return "<TagModel>"
