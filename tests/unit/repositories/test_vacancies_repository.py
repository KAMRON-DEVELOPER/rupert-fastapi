from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.companies.models import CompanyModel
from src.apps.shared.schemas import PaginationQuery
from src.apps.shared.schemas.enums import (
    ApplicationStatus,
    CompanyStatus,
    CompanyType,
    JobSearchStatus,
    Specialization,
    SubmissionType,
    VacancyStatus,
    WorkFormat,
)
from src.apps.vacancies.models import VacancyModel
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.apps.vacancies.schemas.application import ApplicationListParams
from src.apps.vacancies.schemas.vacancy import VacancyListParams


@pytest.mark.asyncio
async def test_vacancies_repository_methods(session: AsyncSession, make_user):
    user = await make_user(email="applicant@example.com")
    company = CompanyModel(
        name="VacCo", country="US", city="NY", type=CompanyType.product_company, status=CompanyStatus.approved
    )
    session.add(company)
    await session.flush()

    created = await VacanciesRepository.create(
        session,
        company.id,
        {
            "title": "Python Dev",
            "description": "desc",
            "submission_type": SubmissionType.profile,
            "specialization": Specialization.backend,
            "work_format": WorkFormat.remote,
            "status": VacancyStatus.open,
        },
    )

    listed = await VacanciesRepository.get_many(
        session,
        PaginationQuery(limit=10, offset=0),
        VacancyListParams(status=VacancyStatus.open),
    )
    assert listed.total == 1

    single = await VacanciesRepository.get_by_id(session, created.id)
    assert single.title == "Python Dev"

    updated = await VacanciesRepository.update(session, created.id, {"title": "Senior Python Dev"})
    assert updated and updated.title == "Senior Python Dev"

    app = await VacanciesRepository.apply_to_vacancy(
        session,
        user.id,
        {"vacancy_id": created.id, "cover_letter": "hello", "status": ApplicationStatus.pending},
    )
    assert app.id is not None

    applications = await VacanciesRepository.get_applications(
        session,
        PaginationQuery(limit=10, offset=0),
        ApplicationListParams(vacancy_id=created.id),
    )
    assert applications.total == 1

    loaded_app = await VacanciesRepository.get_application_by_id(session, app.id)
    assert loaded_app.id == app.id

    changed = await VacanciesRepository.update_application_status(session, app.id, ApplicationStatus.viewed, "ok")
    assert changed and changed.status == ApplicationStatus.viewed

    stats = await VacanciesRepository.get_stats(session)
    assert stats.total == 1
    assert stats.open == 1

    assert await VacanciesRepository.delete(session, created.id) is True
    assert (await session.execute(select(VacancyModel))).scalars().all() == []
