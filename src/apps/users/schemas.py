from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.apps.shared.enums import FollowPolicy, UserRole, UserStatus
from src.utils.exceptions import ValidationException


class AuthProbeResponse(BaseModel):
    is_authenticated: bool


class EmailAuthSchema(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=8, max_length=24, description="First name should be long between 8 and 24")
    last_name: Optional[str] = Field(default=None, min_length=8, max_length=24, description="Last name should be long between 8 and 24")
    email: EmailStr
    password: str = Field(min_length=8, max_length=24, description="Password should be long between 8 and 24")


class UserResponse(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: Optional[str] = None
    username: str
    email: str
    password: str
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    banner_color: Optional[str] = None
    birthdate: Optional[datetime] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    role: UserRole
    status: UserStatus
    follow_policy: FollowPolicy
    followers_count: int
    followings_count: int
    feeds_count: Optional[int] = 0


class UserUpdateSchema(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    follow_policy: FollowPolicy = FollowPolicy.auto_accept
    remove_avatar: bool = False
    remove_banner: bool = False

    @field_validator("email")
    def validate_email(cls, value: Optional[str]):
        return value

    @field_validator("password")
    def validate_password(cls, value: Optional[str]):
        return value

    @field_validator("first_name")
    def validate_first_name(cls, value: Optional[str]):
        return value

    @field_validator("last_name")
    def validate_last_name(cls, value: Optional[str]):
        return value

    @field_validator("birthdate")
    def validate_birthdate(cls, value: Optional[datetime]):
        if value is not None:
            min_age_date = datetime.now(timezone.utc) - timedelta(days=12 * 365)
            max_age_date = datetime.now(timezone.utc) - timedelta(days=100 * 365)
            if not (max_age_date <= value <= min_age_date):
                raise ValidationException(detail="Birthdate must be between 12 and 100 years ago.")
        return value


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_agent: Optional[str]
    ip_addr: Optional[str]
    device_name: Optional[str]
    refresh_token: str
    is_active: bool
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime
