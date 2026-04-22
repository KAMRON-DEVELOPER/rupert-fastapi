from uuid import UUID

from pydantic import BaseModel

from src.apps.shared.enums import ApplicationStatus
from src.apps.shared.schemas import BaseOut
from src.apps.users.schemas import ResumeCardOut, UserCardOut
from src.apps.vacancies.schemas.vacancy import VacancyCardOut


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class ApplicationIn(BaseModel):
    vacancy_id: UUID
    resume_id: UUID | None = None
    cover_letter: str | None = None


class ApplicationFilters(BaseModel):
    vacancy_id: UUID | None = None
    applicant_id: UUID | None = None
    status: ApplicationStatus | None = None


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
