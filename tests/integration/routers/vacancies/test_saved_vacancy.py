from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient

from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_save_and_unsave_vacancy_updates_response_flags(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
):
    await make_user()
    company = await create_company(name="Saved Vacancy Company")
    vacancy = await create_vacancy(company["id"], title="Saved Vacancy")

    save_res = await client.post(f"/api/v1/vacancies/{vacancy['id']}/save")
    assert save_res.status_code == 200
    assert save_res.json()["message"] == "Vacancy saved successfully"

    duplicate_res = await client.post(f"/api/v1/vacancies/{vacancy['id']}/save")
    assert duplicate_res.status_code == 409

    detail_res = await client.get(f"/api/v1/vacancies/{vacancy['id']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["isSaved"] is True
    assert detail_res.json()["hasApplied"] is False

    list_res = await client.get("/api/v1/vacancies/")
    assert list_res.status_code == 200
    assert list_res.json()["data"][0]["isSaved"] is True

    unsave_res = await client.delete(f"/api/v1/vacancies/{vacancy['id']}/save")
    assert unsave_res.status_code == 200
    assert unsave_res.json()["message"] == "Vacancy unsaved successfully"

    missing_saved_res = await client.delete(
        f"/api/v1/vacancies/{vacancy['id']}/save"
    )
    assert missing_saved_res.status_code == 404


@pytest.mark.integration
async def test_save_vacancy_requires_auth(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
):
    await make_user()
    company = await create_company(name="Save Auth Company")
    vacancy = await create_vacancy(company["id"], title="Save Auth Vacancy")
    client.cookies.clear()

    save_res = await client.post(f"/api/v1/vacancies/{vacancy['id']}/save")
    assert save_res.status_code == 401

    unsave_res = await client.delete(f"/api/v1/vacancies/{vacancy['id']}/save")
    assert unsave_res.status_code == 401
