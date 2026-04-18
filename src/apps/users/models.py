from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import TIMESTAMP, Boolean, CheckConstraint, Date, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func, literal_column, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from src.apps.shared.enums import (
    EmploymentType,
    FollowPolicy,
    FollowStatus,
    JobSearchStatus,
    ProficiencyLevel,
    Provider,
    SalaryCurrency,
    Specialization,
    UserRole,
    UserStatus,
    WorkFormat,
)
from src.apps.shared.models import Base, BaseModel, WithLocation

if TYPE_CHECKING:
    from src.apps.chats.models import ChatMessageModel, ChatModel, ChatParticipantModel
    from src.apps.companies.models import CompanyMemberModel
    from src.apps.feeds.models import FeedEngagementModel, FeedModel
    from src.apps.groups.models import GroupMessageModel, GroupModel, GroupParticipantModel
    from src.apps.posts.models import PostCommentModel, PostEngagementModel, PostModel
    from src.apps.shared.models import SkillModel
    from src.apps.vacancies.models import ApplicationModel, SavedVacancyModel


class FollowModel(BaseModel):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_follower_following"),)

    follower_id: Mapped[UUID] = mapped_column(ForeignKey(column="users.id", ondelete="CASCADE"))
    following_id: Mapped[UUID] = mapped_column(ForeignKey(column="users.id", ondelete="CASCADE"))
    status: Mapped[FollowStatus] = mapped_column(Enum(FollowStatus, name="follow_status"), default=FollowStatus.accepted)

    # Relationships
    follower: Mapped[UserModel] = relationship(back_populates="following_links", foreign_keys=[follower_id])
    following: Mapped[UserModel] = relationship(back_populates="follower_links", foreign_keys=[following_id])

    def __repr__(self):
        return "<FollowModel>"


class ResumeSkillLink(BaseModel):
    __tablename__ = "resume_skill_links"
    __table_args__ = (UniqueConstraint("resume_id", "skill_id", name="uq_resume_skill"),)

    resume_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"))
    skill_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"))
    proficiency: Mapped[ProficiencyLevel] = mapped_column(Enum(ProficiencyLevel, name="proficiency_level"), nullable=False)
    last_used_at: Mapped[date | None] = mapped_column(Date)

    # Relationships
    resume: Mapped[ResumeModel] = relationship(back_populates="skill_links")
    skill: Mapped[SkillModel] = relationship(back_populates="resume_links")

    def __repr__(self):
        return "<ResumeSkillLink>"


class ResumeModel(BaseModel, WithLocation):
    __tablename__ = "resumes"
    __table_args__ = (
        CheckConstraint(
            "salary_expectation_min <= salary_expectation_max",
            name="chk_resume_salary_expectation_range",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)

    specialization: Mapped[Specialization] = mapped_column(
        Enum(Specialization, name="specialization"),
        index=True,
        nullable=False,
    )
    salary_expectation_min: Mapped[int | None] = mapped_column(Integer, index=True)
    salary_expectation_max: Mapped[int | None] = mapped_column(Integer, index=True)
    salary_currency: Mapped[SalaryCurrency | None] = mapped_column(Enum(SalaryCurrency, name="salary_currency"))
    work_format: Mapped[WorkFormat | None] = mapped_column(Enum(WorkFormat, name="work_format"))
    employment_type: Mapped[EmploymentType | None] = mapped_column(Enum(EmploymentType, name="employment_type"), index=True)

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="resumes")
    skill_links: Mapped[list[ResumeSkillLink]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    skills: Mapped[list[SkillModel]] = relationship(secondary="resume_skill_links", back_populates="resumes", viewonly=True)
    applications: Mapped[list[ApplicationModel]] = relationship(back_populates="resume")

    def __repr__(self):
        return f"<ResumeModel {self.title}>"


class UserSkillLink(BaseModel):
    __tablename__ = "user_skill_links"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    proficiency: Mapped[ProficiencyLevel] = mapped_column(Enum(ProficiencyLevel, name="proficiency_level"), nullable=False)
    last_used_at: Mapped[date | None] = mapped_column(Date)

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="skill_links")
    skill: Mapped[SkillModel] = relationship(back_populates="user_links")

    def __repr__(self):
        return "<UserSkillLink>"


class WorkExperienceModel(BaseModel):
    __tablename__ = "work_experiences"
    __table_args__ = (CheckConstraint("ended_at IS NULL OR started_at <= ended_at", name="chk_work_experience_date_range"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str | None] = mapped_column(String(128))
    position: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    ended_at: Mapped[date | None] = mapped_column(Date)

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="work_experiences")

    def __repr__(self):
        return "<WorkExperienceModel>"


class OAuthUserModel(Base):
    __tablename__ = "oauth_users"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),)

    id: Mapped[str] = mapped_column(String(length=255), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    provider: Mapped[Provider] = mapped_column(Enum(Provider, name="provider"), nullable=False)
    username: Mapped[str | None] = mapped_column(String(length=128))
    email: Mapped[str | None] = mapped_column(String(length=128))
    picture: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="oauth_users")

    def __repr__(self):
        return "<OAuthUserModel>"


class UserModel(BaseModel, WithLocation):
    __tablename__ = "users"

    # Auth & Identity
    email: Mapped[str] = mapped_column(String(length=128), nullable=False, index=True, unique=True)
    email_verified: Mapped[bool] = mapped_column(default=False)
    password_hash: Mapped[str | None] = mapped_column(String(length=255))

    # Profile
    first_name: Mapped[str] = mapped_column(String(length=64), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(length=64), nullable=False)
    headline: Mapped[str | None] = mapped_column(String(120))
    birthdate: Mapped[date | None] = mapped_column(Date)
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    banner_url: Mapped[str | None] = mapped_column(Text)

    # Specialization
    specialization: Mapped[Specialization | None] = mapped_column(Enum(Specialization, index=True, name="specialization"))

    # Contact
    phone_number: Mapped[str | None] = mapped_column(String(32))
    github_url: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    portfolio_url: Mapped[str | None] = mapped_column(Text)

    # System
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.user, nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"),
        default=UserStatus.pending_verification,
        nullable=False,
    )
    follow_policy: Mapped[FollowPolicy] = mapped_column(
        Enum(FollowPolicy, name="follow_policy"),
        default=FollowPolicy.auto_accept,
        nullable=False,
    )
    job_search_status: Mapped[JobSearchStatus] = mapped_column(
        Enum(JobSearchStatus, name="job_search_status"),
        default=JobSearchStatus.not_looking,
        nullable=False,
    )

    # Relationships
    oauth_users: Mapped[list[OAuthUserModel]] = relationship(back_populates="user", cascade="all, delete-orphan")
    resumes: Mapped[list[ResumeModel]] = relationship(back_populates="user", cascade="all, delete-orphan")
    skill_links: Mapped[list[UserSkillLink]] = relationship(back_populates="user", cascade="all, delete-orphan")
    skills: Mapped[list[SkillModel]] = relationship(secondary="user_skill_links", back_populates="users", viewonly=True)
    work_experiences: Mapped[list[WorkExperienceModel]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list[SessionModel]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activities: Mapped[list[ActivityModel]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # Following
    follower_links: Mapped[list[FollowModel]] = relationship(
        back_populates="following",
        foreign_keys="[FollowModel.following_id]",
        cascade="all, delete-orphan",
    )
    following_links: Mapped[list[FollowModel]] = relationship(
        back_populates="follower",
        foreign_keys="[FollowModel.follower_id]",
        cascade="all, delete-orphan",
    )

    # Jobs
    applications: Mapped[list[ApplicationModel]] = relationship(back_populates="applicant", passive_deletes=True)
    saved_vacancies: Mapped[list[SavedVacancyModel]] = relationship(back_populates="user", passive_deletes=True)
    company_memberships: Mapped[list[CompanyMemberModel]] = relationship(back_populates="user", passive_deletes=True)

    # Feeds
    feeds: Mapped[list[FeedModel]] = relationship(back_populates="author", passive_deletes=True)
    feed_engagements: Mapped[list[FeedEngagementModel]] = relationship(back_populates="user", passive_deletes=True)

    # Posts
    posts: Mapped[list[PostModel]] = relationship(back_populates="author", passive_deletes=True)
    post_engagements: Mapped[list[PostEngagementModel]] = relationship(back_populates="user", passive_deletes=True)
    post_comments: Mapped[list[PostCommentModel]] = relationship(back_populates="user", passive_deletes=True)

    # Groups
    groups: Mapped[list[GroupModel]] = relationship(secondary="group_participants", back_populates="users", viewonly=True)
    group_messages: Mapped[list[GroupMessageModel]] = relationship(back_populates="sender")
    group_participants: Mapped[list[GroupParticipantModel]] = relationship(back_populates="user", passive_deletes=True)

    # Chats
    chats: Mapped[list[ChatModel]] = relationship(secondary="chat_participants", back_populates="users", viewonly=True)
    chat_messages: Mapped[list[ChatMessageModel]] = relationship(back_populates="sender")
    chat_participants: Mapped[list[ChatParticipantModel]] = relationship(back_populates="user", passive_deletes=True)

    # Computed
    followers_count: Mapped[int] = column_property(
        select(func.count(FollowModel.id))
        .where(
            FollowModel.following_id == literal_column("users.id"),
        )
        .correlate_except(FollowModel)
        .scalar_subquery()
    )
    followings_count: Mapped[int] = column_property(
        select(func.count(FollowModel.id))
        .where(
            FollowModel.follower_id == literal_column("users.id"),
        )
        .correlate_except(FollowModel)
        .scalar_subquery()
    )

    def __repr__(self):
        return f"<UserModel {self.first_name} {self.last_name}>"


class SessionModel(BaseModel):
    __tablename__ = "sessions"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    user_agent: Mapped[str | None] = mapped_column(Text)
    ip_addr: Mapped[str | None] = mapped_column(String(45))
    device_name: Mapped[str | None] = mapped_column(String(128))
    refresh_token: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_activity_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="sessions")

    def __repr__(self):
        return f"<SessionModel id={self.id}>"


class ActivityModel(BaseModel):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("user_id", "activity_date", name="uq_user_activity_date"),)

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    last_activity_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    user: Mapped[UserModel] = relationship(back_populates="activities")
