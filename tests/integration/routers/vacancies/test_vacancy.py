from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel
from src.apps.vacancies.models import VacancyModel


@pytest.mark.integration
async def test_vacancy_create_list_detail_update_and_delete(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
    skill: SkillModel,
):
    await make_user()
    company = await create_company(name="Vacancy CRUD Company")

    created = await create_vacancy(
        company["id"],
        title="Backend Engineer",
        skills=[
            {
                "skillId": str(skill.id),
                "proficiency": "advanced",
                "yearsOfExperienceMin": 2,
                "isRequired": True,
            }
        ],
    )
    vacancy_id = created["id"]
    assert created["title"] == "Backend Engineer"
    assert created["company"]["id"] == company["id"]
    assert created["skillLinks"][0]["skill"]["name"] == "Python"

    list_res = await client.get(
        "/api/v1/vacancies/",
        params={"title": "Backend", "status": "open", "limit": 1},
    )
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["data"][0]["id"] == vacancy_id

    detail_res = await client.get(f"/api/v1/vacancies/{vacancy_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["skillLinks"][0]["proficiency"] == "advanced"

    patch_res = await client.patch(
        f"/api/v1/vacancies/{vacancy_id}",
        json={"title": "Senior Backend Engineer", "salaryMax": 5_000},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Senior Backend Engineer"
    assert patch_res.json()["salaryMax"] == 5_000

    delete_res = await client.delete(f"/api/v1/vacancies/{vacancy_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["message"] == "Vacancy deleted successfully"

    deleted = await session.scalar(
        select(VacancyModel).where(VacancyModel.id == UUID(str(vacancy_id)))
    )
    assert deleted is None


@pytest.mark.integration
async def test_vacancy_list_filters_by_company_location_salary_and_skill(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
    skill: SkillModel,
):
    await make_user()
    first_company = await create_company(name="Filter Company")
    second_company = await create_company(name="Other Filter Company")
    vacancy = await create_vacancy(
        first_company["id"],
        title="Remote Backend Engineer",
        salaryMin=3_000,
        salaryMax=6_000,
        workFormat="remote",
        city="Tashkent",
        skills=[{"skillId": str(skill.id), "proficiency": "intermediate"}],
    )
    await create_vacancy(
        second_company["id"],
        title="Frontend Engineer",
        specialization="frontend",
        salaryMin=800,
        salaryMax=1_500,
        workFormat="onsite",
        city="Samarkand",
        skills=[],
    )

    res = await client.get(
        "/api/v1/vacancies/",
        params={
            "companyId": first_company["id"],
            "country": "UZ",
            "city": "Tashkent",
            "salaryMin": 5_000,
            "skillIds": str(skill.id),
            "workFormat": "remote",
        },
    )
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert [item["id"] for item in res.json()["data"]] == [vacancy["id"]]


@pytest.mark.integration
async def test_vacancy_permission_validation_and_missing_resource_paths(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
    vacancy_payload: Callable[..., dict[str, object]],
):
    owner = await make_user(email="vacancy-owner@example.com")
    company = await create_company(name="Vacancy Permissions Company")
    vacancy = await create_vacancy(company["id"], title="Owned Vacancy")

    client.cookies.clear()
    unauth_create_res = await client.post(
        f"/api/v1/vacancies/companies/{company['id']}",
        json=vacancy_payload(title="No Auth Vacancy"),
    )
    assert unauth_create_res.status_code == 401

    other = await make_user(
        email="vacancy-other@example.com",
        first_name="Other",
        with_session=False,
    )
    await authenticate_as(client, session, other)

    create_forbidden_res = await client.post(
        f"/api/v1/vacancies/companies/{company['id']}",
        json=vacancy_payload(title="Forbidden Vacancy"),
    )
    assert create_forbidden_res.status_code == 403

    patch_res = await client.patch(
        f"/api/v1/vacancies/{vacancy['id']}", json={"title": "Nope"}
    )
    assert patch_res.status_code == 403

    delete_res = await client.delete(f"/api/v1/vacancies/{vacancy['id']}")
    assert delete_res.status_code == 403

    await authenticate_as(client, session, owner)
    missing_id = uuid4()

    detail_res = await client.get(f"/api/v1/vacancies/{missing_id}")
    assert detail_res.status_code == 404

    update_missing_res = await client.patch(
        f"/api/v1/vacancies/{missing_id}", json={"title": "Missing"}
    )
    assert update_missing_res.status_code == 404

    invalid_salary_res = await client.post(
        f"/api/v1/vacancies/companies/{company['id']}",
        json=vacancy_payload(salaryMin=5_000, salaryMax=4_000),
    )
    assert invalid_salary_res.status_code == 422
