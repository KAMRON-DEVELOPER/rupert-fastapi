from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.apps.shared.schemas import BaseModelResponse, RequestSchema
from src.apps.shared.schemas.enums import ApplicationStatus
from src.apps.users.schemas.resume import ResumeResponse
from src.apps.users.schemas.user import UserSummaryResponse
from src.apps.vacancies.schemas.vacancy import VacancySummary


class ApplicationListParams(RequestSchema):
    vacancy_id: UUID | None = None
    applicant_id: UUID | None = None
    status: ApplicationStatus | None = None


applicationListDep = Annotated[ApplicationListParams, Depends()]


class ApplicationCreateRequest(RequestSchema):
    resume_id: UUID | None = None
    cover_letter: str | None = None


class ApplicationUpdateRequest(RequestSchema):
    resume_id: UUID | None = None
    cover_letter: str | None = None


class ApplicationStatusUpdateRequest(RequestSchema):
    status: ApplicationStatus
    recruiter_note: str | None = None


class ApplicationSummaryResponse(BaseModelResponse):
    vacancy_id: UUID
    applicant_id: UUID
    status: ApplicationStatus
    cover_letter: str | None
    vacancy: VacancySummary
    resume: ResumeResponse | None


class ApplicationDetailResponse(ApplicationSummaryResponse):
    applicant: UserSummaryResponse
    recruiter_note: str | None
