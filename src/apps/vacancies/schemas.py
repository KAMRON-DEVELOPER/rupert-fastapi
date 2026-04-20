from uuid import UUID

from pydantic import AnyUrl, BaseModel, Field, field_validator

from src.apps.companies.schemas.company import CompanyCardOut
from src.apps.shared.enums import ApplicationStatus, EmploymentType, PaymentFrequency, ProficiencyLevel, SalaryCurrency, Specialization, SubmissionType, VacancyStatus, WorkFormat
from src.apps.shared.schemas import BaseOut, ORMSchema, SkillOut
from src.apps.users.schemas import ResumeCardOut, UserCardOut


# ---------------------------------------------------------------------------
# VacancySkillLink
# ---------------------------------------------------------------------------
class VacancySkillLinkIn(BaseModel):
    skill_id: UUID
    proficiency: ProficiencyLevel
    years_of_experience_min: float | None = None
    is_required: bool = True


class VacancySkillLinkOut(ORMSchema):
    skill: SkillOut
    proficiency: ProficiencyLevel
    years_of_experience_min: float | None
    is_required: bool


# ---------------------------------------------------------------------------
# Vacancy
# ---------------------------------------------------------------------------
class VacancyIn(BaseModel):
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

    country: str = Field(max_length=64)
    city: str = Field(max_length=64)

    status: VacancyStatus = VacancyStatus.draft

    skills: list[VacancySkillLinkIn] = Field(default_factory=list)

    @field_validator("salary_max")
    @classmethod
    def max_gte_min(cls, v: int | None, info) -> int | None:
        min_ = info.data.get("salary_min")
        if v is not None and min_ is not None and v < min_:
            raise ValueError("salary_max must be >= salary_min")
        return v


class VacancyUpdateIn(BaseModel):
    title: str | None = Field(default=None, max_length=128)
    description: str | None = None

    external_apply_url: AnyUrl | None = None
    submission_type: SubmissionType | None = None

    specialization: Specialization | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: SalaryCurrency | None = None
    payment_frequency: PaymentFrequency | None = None

    years_of_experience_min: float | None = None
    work_format: WorkFormat | None = None
    work_hours_per_week: int | None = None
    employment_type: EmploymentType | None = None

    country: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=64)

    status: VacancyStatus | None = None


class VacancyCardOut(BaseModel):
    company_name: str

    title: str

    specialization: Specialization
    salary_min: int | None
    salary_max: int | None
    salary_currency: SalaryCurrency | None
    payment_frequency: PaymentFrequency | None

    country: str
    city: str

    status: VacancyStatus

    years_of_experience_min: float | None = None
    work_format: WorkFormat
    employment_type: EmploymentType
    work_hours_per_week: int | None = None

    is_saved: bool = False
    has_applied: bool = False


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class ApplicationIn(BaseModel):
    vacancy_id: UUID
    resume_id: UUID | None = None
    cover_letter: str | None = None


class ApplicationStatusUpdateIn(BaseModel):
    status: ApplicationStatus
    recruiter_note: str | None = None


class ApplicationOut(BaseOut):
    vacancy_id: UUID
    applicant_id: UUID
    status: ApplicationStatus
    cover_letter: str | None

    vacancy: VacancyCardOut
    resume: ResumeCardOut | None


class ApplicationDetailOut(ApplicationOut):
    applicant: UserCardOut
    recruiter_note: str | None


# ---------------------------------------------------------------------------
# Saved Vacancy
# ---------------------------------------------------------------------------
class SavedVacancyOut(BaseOut):
    vacancy: VacancyCardOut
