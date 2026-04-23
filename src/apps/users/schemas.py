from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, AliasGenerator, BaseModel, ConfigDict, EmailStr, Field, ValidationInfo, computed_field, field_validator
from pydantic.alias_generators import to_camel

from src.apps.shared.enums import EmploymentType, FollowPolicy, JobSearchStatus, ProficiencyLevel, Provider, SalaryCurrency, Specialization, UserRole, UserStatus, WorkFormat
from src.apps.shared.schemas import BaseOut, CamelCaseOut, ORMSchema, SkillOut
from src.core.exceptions import ValidationException


def validate_first_name(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("First name should be long between 8 and 24")
    return v


def validate_last_name(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("Last name should be long between 8 and 24")
    return v


def validate_password(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("Password should be long between 8 and 24")
    return v


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class AuthProbeOut(CamelCaseOut):
    is_authenticated: bool


class PasswordSetupIn(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 8 or len(v) > 24:
            raise ValueError("Password should be long between 8 and 24")
        return v


class EmailAuthIn(BaseModel):
    email: EmailStr
    password: Annotated[str, AfterValidator(validate_password)]
    first_name: Annotated[str | None, AfterValidator(validate_first_name)] = None
    last_name: Annotated[str | None, AfterValidator(validate_last_name)] = None

    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=to_camel))


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------
class OAuthUserOut(BaseOut):
    user_id: UUID
    provider: Provider
    username: str | None
    email: str | None
    picture: str | None


# ---------------------------------------------------------------------------
# ResumeSkillLink
# ---------------------------------------------------------------------------
class ResumeSkillLinkIn(BaseModel):
    skill_id: UUID
    proficiency: ProficiencyLevel
    last_used_at: date | None = None


class ResumeSkillLinkOut(ORMSchema):
    resume_id: UUID
    skill: SkillOut
    proficiency: ProficiencyLevel
    last_used_at: date | None


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------
class ResumeIn(BaseModel):
    title: str = Field(max_length=128)
    summary: str | None = None
    specialization: Specialization
    country: str = Field(max_length=64)
    city: str = Field(max_length=64)
    salary_expectation_min: int | None = Field(default=None, ge=0)
    salary_expectation_max: int | None = Field(default=None, ge=0)
    salary_currency: SalaryCurrency | None = None
    work_format: WorkFormat | None = None
    employment_type: EmploymentType | None = None
    skills: list[ResumeSkillLinkIn] = Field(default_factory=list)

    @field_validator("salary_expectation_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info: ValidationInfo) -> int | None:
        min_ = info.data.get("salary_expectation_min")
        if v and min_ and v < min_:
            raise ValueError("salary_expectation_max must be >= salary_expectation_min")
        return v


class ResumeUpdateIn(BaseModel):
    title: str | None = Field(default=None, max_length=128)
    summary: str | None = None
    specialization: Specialization | None = None
    country: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=64)
    salary_expectation_min: int | None = Field(default=None, ge=0)
    salary_expectation_max: int | None = Field(default=None, ge=0)
    salary_currency: SalaryCurrency | None = None
    work_format: WorkFormat | None = None
    employment_type: EmploymentType | None = None
    skills: list[ResumeSkillLinkIn] | None = None


class ResumeOut(BaseOut):
    user_id: UUID
    title: str
    summary: str | None
    specialization: Specialization
    country: str
    city: str
    salary_expectation_min: int | None
    salary_expectation_max: int | None
    salary_currency: SalaryCurrency | None
    work_format: WorkFormat | None
    employment_type: EmploymentType | None
    skills: list[ResumeSkillLinkOut]


class ResumeCardOut(BaseOut):
    user_id: UUID
    title: str
    specialization: Specialization
    country: str
    city: str
    salary_expectation_min: int | None
    salary_expectation_max: int | None
    salary_currency: SalaryCurrency | None
    work_format: WorkFormat | None
    employment_type: EmploymentType | None


# ---------------------------------------------------------------------------
# UserSkillLink
# ---------------------------------------------------------------------------
class UserSkillLinkIn(BaseModel):
    skill_id: UUID
    proficiency: ProficiencyLevel
    last_used_at: date | None = None


class UserSkillLinkOut(ORMSchema):
    skill: SkillOut
    proficiency: ProficiencyLevel
    last_used_at: date | None


# ---------------------------------------------------------------------------
# Work Experience
# ---------------------------------------------------------------------------
class WorkExperienceIn(BaseModel):
    company_name: str = Field(max_length=128)
    location: str | None = Field(default=None, max_length=128)
    position: str = Field(max_length=128)
    description: str | None = None
    started_at: date
    ended_at: date | None = None

    @field_validator("ended_at")
    @classmethod
    def ended_after_started(cls, v: date | None, info) -> date | None:
        if v and info.data.get("started_at") and v < info.data["started_at"]:
            raise ValueError("ended_at must be after started_at")
        return v


class WorkExperienceOut(BaseOut):
    user_id: UUID
    company_name: str
    location: str | None
    position: str
    description: str | None
    started_at: date
    ended_at: date | None

    @computed_field
    @property
    def is_current(self) -> bool:
        return self.ended_at is None


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class UserCardOut(BaseOut):
    first_name: str
    last_name: str | None
    headline: str | None
    avatar_url: str | None
    country: str | None
    city: str | None
    specialization: Specialization | None
    job_search_status: JobSearchStatus
    followers_count: int
    followings_count: int


class UserOut(BaseOut):
    # Auth & Identity
    email: str
    email_verified: bool
    # Profile
    first_name: str
    last_name: str | None
    headline: str | None
    birthdate: date | None
    bio: str | None
    avatar_url: str | None
    banner_url: str | None
    country: str | None
    city: str | None
    # Specialization
    specialization: Specialization | None
    # Contact
    phone_number: str | None
    github_url: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    # System
    role: UserRole
    status: UserStatus
    follow_policy: FollowPolicy
    job_search_status: JobSearchStatus
    # Relationships
    resumes: list[ResumeOut]
    skills: list[UserSkillLinkOut]
    work_experiences: list[WorkExperienceOut]
    # Computed
    followers_count: int
    followings_count: int


class UserUpdateIn(BaseModel):
    # Profile
    first_name: str | None = Field(default=None, max_length=64)
    last_name: str | None = Field(default=None, max_length=64)
    headline: str | None = Field(default=None, max_length=120)
    birthdate: date | None = None
    bio: str | None = None
    country: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=64)
    # Specialization
    specialization: Specialization | None = None
    # Contact
    phone_number: str | None = Field(default=None, max_length=32)
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    # System
    follow_policy: FollowPolicy | None = None
    job_search_status: JobSearchStatus | None = None

    @field_validator("birthdate")
    def validate_birthdate(cls, value: datetime | None):
        if value is not None:
            min_age_date = datetime.now(timezone.utc) - timedelta(days=12 * 365)
            max_age_date = datetime.now(timezone.utc) - timedelta(days=100 * 365)
            if not (max_age_date <= value <= min_age_date):
                raise ValidationException(detail="Birthdate must be between 12 and 100 years ago.")
        return value


class UserAvatarUpdateIn(BaseModel):
    avatar_url: str


class UserBannerUpdateIn(BaseModel):
    banner_url: str


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
class SessionOut(BaseOut):
    user_id: UUID
    user_agent: str | None
    ip_addr: str | None
    device_name: str | None
    is_active: bool
    last_activity_at: datetime
