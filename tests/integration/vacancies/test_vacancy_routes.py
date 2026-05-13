import pytest

from src.apps.companies.models import CompanyModel
from src.apps.shared.schemas.enums import (
    CompanyStatus,
    CompanyType,
    Specialization,
    SubmissionType,
    VacancyStatus,
    WorkFormat,
)
from src.apps.vacancies.models import VacancyModel


@pytest.mark.asyncio
async def test_list_and_get_vacancy(client, session):
    company = CompanyModel(
        name="VacCmp", type=CompanyType.product_company, status=CompanyStatus.approved, country="US", city="NY"
    )
    session.add(company)
    await session.flush()
    vacancy = VacancyModel(
        company_id=company.id,
        title="Role",
        description="desc",
        submission_type=SubmissionType.profile,
        specialization=Specialization.backend,
        work_format=WorkFormat.remote,
        status=VacancyStatus.open,
    )
    session.add(vacancy)
    await session.commit()

    res = await client.get("/api/v1/vacancies/?limit=10&offset=0")
    assert res.status_code == 200
    assert res.json()["total"] == 1

    detail = await client.get(f"/api/v1/vacancies/{vacancy.id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == str(vacancy.id)


@pytest.mark.asyncio
async def test_get_vacancy_not_found(client):
    res = await client.get("/api/v1/vacancies/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 500
