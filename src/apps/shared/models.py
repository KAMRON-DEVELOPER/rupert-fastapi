from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, TIMESTAMP
from sqlalchemy import UUID as PG_UUID
from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from src.apps.feeds.models import FeedModel, FeedTagLink
    from src.apps.posts.models import PostModel, PostTagLink
    from src.apps.users.models import ResumeModel, ResumeSkillLink, UserModel, UserSkillLink
    from src.apps.vacancies.models import VacancyModel, VacancySkillLink


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), default=uuid4, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())


class WithLocation(Base):
    __abstract__ = True

    country: Mapped[Optional[str]] = mapped_column(String(64))
    city: Mapped[Optional[str]] = mapped_column(String(64))


class MessageBaseModel(BaseModel):
    __abstract__ = True

    sender_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(column="users.id", ondelete="CASCADE"))
    message: Mapped[Optional[str]] = mapped_column(Text)
    image_urls: Mapped[Optional[list[str]]] = mapped_column(ARRAY(item_type=String))
    video_urls: Mapped[Optional[list[str]]] = mapped_column(ARRAY(item_type=String))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    def __repr__(self):
        return "<MessageBaseModel>"


class TagModel(BaseModel):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(length=24), unique=True, nullable=False)

    # Relationships
    post_links: Mapped[list["PostTagLink"]] = relationship(back_populates="tag", cascade="all, delete-orphan")
    posts: Mapped[list["PostModel"]] = relationship(secondary="post_tag_links", back_populates="tags")

    feed_links: Mapped[list["FeedTagLink"]] = relationship(back_populates="tag", cascade="all, delete-orphan")
    feeds: Mapped[list["FeedModel"]] = relationship(secondary="feed_tag_links", back_populates="tags")

    def __repr__(self):
        return "<TagModel>"


class SkillModel(BaseModel):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(length=64), nullable=False, index=True, unique=True)

    # Relationships
    user_links: Mapped[list["UserSkillLink"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    users: Mapped[list["UserModel"]] = relationship(secondary="user_skill_links", back_populates="skills", viewonly=True)

    resume_links: Mapped[list["ResumeSkillLink"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    resumes: Mapped[list["ResumeModel"]] = relationship(secondary="resume_skill_links", back_populates="skills", viewonly=True)

    vacancy_links: Mapped[list["VacancySkillLink"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    vacancies: Mapped[list["VacancyModel"]] = relationship(secondary="vacancy_skill_links", back_populates="skills", viewonly=True)

    def __repr__(self):
        return f"<SkillModel {self.name}>"
