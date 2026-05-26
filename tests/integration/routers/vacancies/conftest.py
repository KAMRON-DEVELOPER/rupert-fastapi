from collections.abc import Awaitable, Callable
from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel
from src.apps.users.repositories.session import SessionsRepository
from src.dependencies.proactive_refresh import create_token
from tests.conftest import set_client_cookie


async def _authenticate_as(
    client: AsyncClient, session: AsyncSession, user: UserModel
) -> str:
    access_token = create_token(user.id, "access")
    refresh_token = create_token(user.id, "refresh")

    await SessionsRepository.create(
        session,
        refresh_token,
        user.id,
        user_agent="pytest",
        ip_addr="127.0.0.1",
        device_name="test",
    )
    await session.flush()

    set_client_cookie(client, "access_token", access_token)
    set_client_cookie(client, "refresh_token", refresh_token)

    return refresh_token


async def _create_skill(session: AsyncSession, name: str) -> SkillModel:
    record = SkillModel(name=name)

    session.add(record)
    await session.flush()

    return record


def _location_ids(
    default_location: dict[str, object], overrides: dict[str, object]
) -> dict[str, object]:
    country = cast(Any, default_location["country"])
    cities = cast(dict[str, Any], default_location["cities"])
    city_name = str(overrides.pop("city", "Tashkent"))
    overrides.pop("country", None)
    return {"countryId": str(country.id), "cityId": str(cities[city_name].id)}


def _company_payload(
    default_location: dict[str, object], **overrides: object
) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Vacancy Company",
        "tagline": "Hiring better",
        "description": "A company for vacancy tests.",
        "websiteUrl": "https://vacancy-company.example.com",
        "type": "startup",
        "contactEmail": "hello@vacancy-company.example.com",
        **_location_ids(default_location, overrides),
    }
    payload.update(overrides)
    return payload


def _vacancy_payload(
    default_location: dict[str, object], **overrides: object
) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Backend Engineer",
        "description": "Build FastAPI services.",
        "submissionType": "resume",
        "specialization": "backend",
        "salaryMin": 2_000,
        "salaryMax": 4_000,
        "salaryCurrency": "USD",
        "paymentFrequency": "once_a_month",
        "yearsOfExperienceMin": 2,
        "workFormat": "remote",
        "workHoursPerWeek": 40,
        "employmentType": "full_time",
        "status": "open",
        **_location_ids(default_location, overrides),
        "skills": [],
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def authenticate_as() -> Callable[
    [AsyncClient, AsyncSession, UserModel], Awaitable[str]
]:
    return _authenticate_as


@pytest.fixture
def company_payload(
    default_location: dict[str, object],
) -> Callable[..., dict[str, object]]:
    def _payload(**overrides: object) -> dict[str, object]:
        return _company_payload(default_location, **overrides)

    return _payload


@pytest.fixture
def vacancy_payload(
    default_location: dict[str, object],
) -> Callable[..., dict[str, object]]:
    def _payload(**overrides: object) -> dict[str, object]:
        return _vacancy_payload(default_location, **overrides)

    return _payload


@pytest.fixture
def create_company(
    client: AsyncClient, company_payload: Callable[..., dict[str, object]]
) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _create_company(**overrides: object) -> dict[str, Any]:
        res = await client.post(
            "/api/v1/companies/", json=company_payload(**overrides)
        )
        assert res.status_code == 201
        return res.json()

    return _create_company


@pytest.fixture
def create_vacancy(
    client: AsyncClient, vacancy_payload: Callable[..., dict[str, object]]
) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _create_vacancy(
        company_id: str, **overrides: object
    ) -> dict[str, Any]:
        res = await client.post(
            f"/api/v1/vacancies/companies/{company_id}",
            json=vacancy_payload(**overrides),
        )
        assert res.status_code == 201
        return res.json()

    return _create_vacancy


@pytest.fixture
async def skill(session: AsyncSession) -> SkillModel:
    return await _create_skill(session, "Python")


@pytest.fixture
async def another_skill(session: AsyncSession) -> SkillModel:
    return await _create_skill(session, "FastAPI")
