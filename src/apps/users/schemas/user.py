import datetime
from datetime import date
from typing import Annotated
from uuid import UUID

from dateutil.relativedelta import relativedelta
from fastapi import Form
from pydantic import Field, field_validator

from src.apps.shared.schemas import BaseNullableLocationModelResponse
from src.apps.shared.schemas.enums import (
    FollowPolicy,
    JobSearchStatus,
    Specialization,
    UserRole,
    UserStatus,
)
from src.apps.shared.schemas.location import NullableLocationRequest
from src.apps.shared.schemas.skill import SkillLinkResponse
from src.apps.users.schemas.resume import ResumeSummaryResponse
from src.apps.users.schemas.work_experience import WorkExperienceResponse
from src.core.exceptions import ValidationException


class UserUpdateRequest(NullableLocationRequest):
    first_name: str | None = Field(default=None, max_length=64)
    last_name: str | None = Field(default=None, max_length=64)
    headline: str | None = Field(default=None, max_length=120)
    birthdate: date | None = None
    bio: str | None = None
    specialization: Specialization | None = None
    phone_number: str | None = Field(default=None, max_length=32)
    github_url: str | None = None
    telegram_username: str | None = None
    follow_policy: FollowPolicy | None = None
    job_search_status: JobSearchStatus | None = None
    delete_avatar: bool | None = None
    delete_banner: bool | None = None

    @field_validator("birthdate")
    def validate_birthdate(cls, value: date | None):
        if value is None:
            return value

        today = datetime.datetime.now(tz=datetime.UTC).date()
        min_birthdate = today - relativedelta(years=100)
        max_birthdate = today - relativedelta(years=12)

        if not (min_birthdate <= value <= max_birthdate):
            raise ValidationException(
                detail="Birthdate must be between 12 and 100 years ago."
            )

        return value

    @classmethod
    def as_form(
        cls,
        first_name: Annotated[str | None, Form(alias="firstName")] = None,
        last_name: Annotated[str | None, Form(alias="lastName")] = None,
        country_id: Annotated[UUID | None, Form()] = None,
        city_id: Annotated[UUID | None, Form()] = None,
        headline: Annotated[str | None, Form()] = None,
        birthdate: Annotated[date | None, Form()] = None,
        bio: Annotated[str | None, Form()] = None,
        specialization: Annotated[Specialization | None, Form()] = None,
        phone_number: Annotated[str | None, Form(alias="phoneNumber")] = None,
        github_url: Annotated[str | None, Form(alias="githubUrl")] = None,
        telegram_username: Annotated[
            str | None, Form(alias="telegramUsername")
        ] = None,
        follow_policy: Annotated[
            FollowPolicy | None, Form(alias="followPolicy")
        ] = None,
        job_search_status: Annotated[
            JobSearchStatus | None, Form(alias="jobSearchStatus")
        ] = None,
        delete_avatar: Annotated[
            bool | None, Form(alias="deleteAvatar")
        ] = None,
        delete_banner: Annotated[
            bool | None, Form(alias="deleteBanner")
        ] = None,
    ):
        data = {
            "firstName": first_name,
            "lastName": last_name,
            "countryId": country_id,
            "cityId": city_id,
            "headline": headline,
            "birthdate": birthdate,
            "bio": bio,
            "specialization": specialization,
            "phoneNumber": phone_number,
            "githubUrl": github_url,
            "telegramUsername": telegram_username,
            "followPolicy": follow_policy,
            "jobSearchStatus": job_search_status,
            "deleteAvatar": delete_avatar,
            "deleteBanner": delete_banner,
        }
        return cls.model_validate(
            {key: value for key, value in data.items() if value is not None}
        )


class UserSummaryResponse(BaseNullableLocationModelResponse):
    first_name: str
    last_name: str | None
    headline: str | None
    avatar_url: str | None
    specialization: Specialization | None
    job_search_status: JobSearchStatus

    # Computed
    followers_count: int
    followings_count: int


class UserDetailResponse(BaseNullableLocationModelResponse):
    email: str
    email_verified: bool
    first_name: str
    last_name: str | None
    headline: str | None
    birthdate: date | None
    bio: str | None
    avatar_url: str | None
    banner_url: str | None
    specialization: Specialization | None
    phone_number: str | None
    github_url: str | None
    telegram_username: str | None
    role: UserRole
    status: UserStatus
    follow_policy: FollowPolicy
    job_search_status: JobSearchStatus

    # Relationships
    resumes: list[ResumeSummaryResponse]
    skills: list[SkillLinkResponse] = Field(validation_alias="skill_links")
    work_experiences: list[WorkExperienceResponse]

    # Computed
    followers_count: int
    followings_count: int
