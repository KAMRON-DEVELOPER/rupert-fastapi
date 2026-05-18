from datetime import date
from uuid import UUID

from pydantic import Field, computed_field, field_validator

from src.apps.shared.schemas import BaseModelResponse, RequestSchema


class WorkExperienceRequest(RequestSchema):
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


class WorkExperienceUpdateRequest(RequestSchema):
    company_name: str | None = Field(default=None, max_length=128)
    location: str | None = Field(default=None, max_length=128)
    position: str | None = Field(default=None, max_length=128)
    description: str | None = None
    started_at: date | None = None
    ended_at: date | None = None

    @field_validator("ended_at")
    @classmethod
    def ended_after_started(cls, v: date | None, info) -> date | None:
        if v and info.data.get("started_at") and v < info.data["started_at"]:
            raise ValueError("ended_at must be after started_at")
        return v


class WorkExperienceResponse(BaseModelResponse):
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
