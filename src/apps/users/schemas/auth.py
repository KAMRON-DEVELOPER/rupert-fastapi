from datetime import date
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, field_validator

from src.apps.shared.schemas import (
    BaseModelResponse,
    RequestSchema,
    ResponseSchema,
)
from src.apps.shared.schemas.enums import (
    FollowPolicy,
    JobSearchStatus,
    Specialization,
    UserRole,
    UserStatus,
)


def validate_first_name(v: str | None) -> str | None:
    if v and (len(v) < 3 or len(v) > 24):
        raise ValueError("First name should be long between 3 and 24")
    return v


def validate_last_name(v: str | None) -> str | None:
    if v and (len(v) < 3 or len(v) > 24):
        raise ValueError("Last name should be long between 3 and 24")
    return v


def validate_password(v: str | None) -> str | None:
    if v and (len(v) < 3 or len(v) > 24):
        raise ValueError("Password should be long between 3 and 24")
    return v


class AuthProbeResponse(ResponseSchema):
    is_authenticated: bool


class EmailAuthRequest(RequestSchema):
    email: EmailStr
    password: Annotated[str, AfterValidator(validate_password)]
    first_name: Annotated[str | None, AfterValidator(validate_first_name)] = (
        None
    )
    last_name: Annotated[str | None, AfterValidator(validate_last_name)] = None


class EmailAuthResponse(BaseModelResponse):
    email: str
    email_verified: bool
    password_hash: str | None
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


class PasswordSetupRequest(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 8 or len(v) > 24:
            raise ValueError("Password should be long between 8 and 24")
        return v
