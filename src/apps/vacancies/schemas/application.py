from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.apps.shared.schemas import RequestSchema, ResponseSchema
from src.apps.shared.schemas.enums import ApplicationStatus
from src.apps.users.schemas.resume import ResumeSummary
from src.apps.users.schemas.user import UserSummaryResponse
from src.apps.vacancies.schemas.vacancy import VacancySummary


class ApplicationRequest(RequestSchema):
    vacancy_id: UUID
    resume_id: UUID | None = None
    cover_letter: str | None = None


class ApplicationListParams(RequestSchema):
    vacancy_id: UUID | None = None
    applicant_id: UUID | None = None
    status: ApplicationStatus | None = None


applicationListDep = Annotated[ApplicationListParams, Depends()]


class ApplicationStatusUpdateRequest(RequestSchema):
    status: ApplicationStatus
    recruiter_note: str | None = None


class ApplicationSummary(ResponseSchema):
    vacancy_id: UUID
    applicant_id: UUID
    status: ApplicationStatus
    cover_letter: str | None
    vacancy: VacancySummary
    resume: ResumeSummary | None


class ApplicationDetail(ApplicationSummary):
    applicant: UserSummaryResponse
    recruiter_note: str | None
