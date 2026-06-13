from uuid import UUID

from pydantic import Field, ValidationInfo, field_validator

from src.apps.shared.schemas import BaseLocationModelResponse, LocationRequest
from src.apps.shared.schemas.enums import (
    EmploymentType,
    SalaryCurrency,
    Specialization,
    WorkFormat,
)
from src.apps.shared.schemas.location import NullableLocationRequest


class ResumeCreateRequest(LocationRequest):
    title: str = Field(max_length=128)
    summary: str | None = None
    specialization: Specialization
    salary_expectation_min: int | None = Field(default=None, ge=0)
    salary_expectation_max: int | None = Field(default=None, ge=0)
    salary_currency: SalaryCurrency | None = None
    work_format: WorkFormat | None = None
    employment_type: EmploymentType | None = None
    # skills: list[SkillLinkCreateRequest] = Field(default_factory=list)

    @field_validator("salary_expectation_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info: ValidationInfo) -> int | None:
        min_ = info.data.get("salary_expectation_min")
        if v is not None and min_ is not None and v < min_:
            raise ValueError(
                "salary_expectation_max must be >= salary_expectation_min"
            )
        return v


class ResumeUpdateRequest(NullableLocationRequest):
    title: str | None = Field(default=None, max_length=128)
    summary: str | None = None
    specialization: Specialization | None = None
    salary_expectation_min: int | None = Field(default=None, ge=0)
    salary_expectation_max: int | None = Field(default=None, ge=0)
    salary_currency: SalaryCurrency | None = None
    work_format: WorkFormat | None = None
    employment_type: EmploymentType | None = None

    @field_validator("salary_expectation_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info: ValidationInfo) -> int | None:
        min_ = info.data.get("salary_expectation_min")
        if v is not None and min_ is not None and v < min_:
            raise ValueError(
                "salary_expectation_max must be >= salary_expectation_min"
            )
        return v


class ResumeResponse(BaseLocationModelResponse):
    user_id: UUID
    title: str
    summary: str | None
    specialization: Specialization
    salary_expectation_min: int | None
    salary_expectation_max: int | None
    salary_currency: SalaryCurrency | None
    work_format: WorkFormat | None
    employment_type: EmploymentType | None
    # skills: list[SkillLinkResponse] = Field(validation_alias="skill_links")
