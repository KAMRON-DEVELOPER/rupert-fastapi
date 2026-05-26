from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from pydantic import AnyUrl, Field, ValidationInfo, field_validator

from src.apps.companies.schemas.company import CompanySummary
from src.apps.shared.schemas import (
    BaseLocationModelResponse,
    LocationRequest,
    RequestSchema,
)
from src.apps.shared.schemas.enums import (
    EmploymentType,
    PaymentFrequency,
    SalaryCurrency,
    Specialization,
    SubmissionType,
    VacancyStatus,
    WorkFormat,
)
from src.apps.shared.schemas.location import NullableLocationRequest
from src.apps.vacancies.schemas.skill_links import (
    VacancySkillLinkRequest,
    VacancySkillLinkResponse,
)


class VacancyCreateRequest(LocationRequest):
    title: str = Field(max_length=128)
    description: str
    external_apply_url: AnyUrl | None = None
    submission_type: SubmissionType
    specialization: Specialization
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: SalaryCurrency | None = None
    payment_frequency: PaymentFrequency | None = None
    years_of_experience_min: float | None = Field(default=None, ge=0)
    work_format: WorkFormat = WorkFormat.onsite
    work_hours_per_week: int | None = Field(default=None, ge=1, le=168)
    employment_type: EmploymentType = EmploymentType.full_time
    status: VacancyStatus = VacancyStatus.draft
    skills: list[VacancySkillLinkRequest] = Field(default_factory=list)

    @field_validator("salary_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info: ValidationInfo) -> int | None:
        min_ = info.data.get("salary_min")
        if v is not None and min_ is not None and v < min_:
            raise ValueError("salary_max must be >= salary_min")
        return v


class VacancyUpdateRequest(NullableLocationRequest):
    title: str | None = Field(default=None, max_length=128)
    description: str | None = None
    external_apply_url: AnyUrl | None = None
    submission_type: SubmissionType | None = None
    specialization: Specialization | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: SalaryCurrency | None = None
    payment_frequency: PaymentFrequency | None = None
    years_of_experience_min: float | None = Field(default=None, ge=0)
    work_format: WorkFormat | None = None
    work_hours_per_week: int | None = Field(default=None, ge=1, le=168)
    employment_type: EmploymentType | None = None
    status: VacancyStatus | None = None
    skills: list[VacancySkillLinkRequest] | None = None

    @field_validator("salary_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info: ValidationInfo) -> int | None:
        min_ = info.data.get("salary_min")
        if v is not None and min_ is not None and v < min_:
            raise ValueError("salary_max must be >= salary_min")
        return v


class VacancyListParams(RequestSchema):
    company_id: UUID | None = None
    title: str | None = None
    submission_type: SubmissionType | None = None
    specialization: Specialization | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: SalaryCurrency | None = None
    years_of_experience_min: float | None = None
    work_format: WorkFormat | None = None
    employment_type: EmploymentType | None = None
    status: VacancyStatus | None = None
    country_id: UUID | None = None
    city_id: UUID | None = None
    skill_ids: list[UUID] | None = Query(None)


vacancyListDep = Annotated[VacancyListParams, Depends()]


class VacancySummary(BaseLocationModelResponse):
    company: CompanySummary
    title: str
    submission_type: SubmissionType
    specialization: Specialization
    salary_min: int | None
    salary_max: int | None
    salary_currency: SalaryCurrency | None
    years_of_experience_min: float | None = None
    work_format: WorkFormat
    employment_type: EmploymentType
    status: VacancyStatus
    is_saved: bool | None = None
    has_applied: bool | None = None


class VacancyDetail(VacancySummary):
    description: str
    external_apply_url: AnyUrl | None
    work_hours_per_week: int | None = None
    payment_frequency: PaymentFrequency | None
    skill_links: list[VacancySkillLinkResponse]
