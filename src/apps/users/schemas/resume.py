from uuid import UUID

from pydantic import Field, ValidationInfo, field_validator

from src.apps.shared.schemas import BaseModelResponse, RequestSchema
from src.apps.shared.schemas.enums import (
    EmploymentType,
    SalaryCurrency,
    Specialization,
    WorkFormat,
)
from src.apps.users.schemas.skill_links import (
    ResumeSkillLinkRequest,
    ResumeSkillLinkResponse,
)


class ResumeRequest(RequestSchema):
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
    skills: list[ResumeSkillLinkRequest] = Field(default_factory=list)

    @field_validator("salary_expectation_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info: ValidationInfo) -> int | None:
        min_ = info.data.get("salary_expectation_min")
        if v is not None and min_ is not None and v < min_:
            raise ValueError(
                "salary_expectation_max must be >= salary_expectation_min"
            )
        return v


class ResumeUpdateRequest(RequestSchema):
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
    skills: list[ResumeSkillLinkRequest] | None = None

    @field_validator("salary_expectation_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info: ValidationInfo) -> int | None:
        min_ = info.data.get("salary_expectation_min")
        if v is not None and min_ is not None and v < min_:
            raise ValueError(
                "salary_expectation_max must be >= salary_expectation_min"
            )
        return v


class ResumeResponse(BaseModelResponse):
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
    skills: list[ResumeSkillLinkResponse] = Field(
        validation_alias="skill_links"
    )


class ResumeSummary(BaseModelResponse):
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
