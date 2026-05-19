from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.companies.models import CompanyModel
from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_company_create_list_detail_update_and_delete(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
):
    await make_user()

    first = await create_company(name="Rupert Labs")
    second = await create_company(name="Acme Hiring", city="Samarkand")

    assert first["name"] == "Rupert Labs"
    assert first["type"] == "startup"
    assert first["openVacanciesCount"] == 0
    assert first["memberCount"] == 1
    assert first["members"][0]["role"] == "owner"

    list_res = await client.get("/api/v1/companies/", params={"limit": 1})
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 2
    assert len(list_res.json()["data"]) == 1

    filter_res = await client.get(
        "/api/v1/companies/", params={"name": "Rupert", "city": "Tashkent"}
    )
    assert filter_res.status_code == 200
    assert [item["id"] for item in filter_res.json()["data"]] == [first["id"]]

    detail_res = await client.get(f"/api/v1/companies/{first['id']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["members"][0]["user"]["firstName"] == "Test"

    patch_res = await client.patch(
        f"/api/v1/companies/{first['id']}",
        json={"tagline": "Better hiring", "type": "product_company"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["tagline"] == "Better hiring"
    assert patch_res.json()["type"] == "product_company"

    delete_res = await client.delete(f"/api/v1/companies/{second['id']}")
    assert delete_res.status_code == 200
    assert delete_res.json()["message"] == "Company deleted successfully"

    deleted = await session.scalar(
        select(CompanyModel).where(CompanyModel.id == UUID(str(second["id"])))
    )
    assert deleted is None


@pytest.mark.integration
async def test_company_auth_permission_and_missing_resource_paths(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    company_payload: Callable[..., dict[str, object]],
):
    missing_id = uuid4()

    get_missing_res = await client.get(f"/api/v1/companies/{missing_id}")
    assert get_missing_res.status_code == 404

    unauth_create_res = await client.post(
        "/api/v1/companies/", json=company_payload(name="No Auth Company")
    )
    assert unauth_create_res.status_code == 401

    owner = await make_user(email="company-owner@example.com")
    company = await create_company(name="Owned Company")

    other = await make_user(
        email="company-other@example.com",
        first_name="Other",
        with_session=False,
    )
    await authenticate_as(client, session, other)

    patch_res = await client.patch(
        f"/api/v1/companies/{company['id']}", json={"tagline": "Nope"}
    )
    assert patch_res.status_code == 403

    delete_res = await client.delete(f"/api/v1/companies/{company['id']}")
    assert delete_res.status_code == 403

    await authenticate_as(client, session, owner)
    owner_delete_res = await client.delete(f"/api/v1/companies/{company['id']}")
    assert owner_delete_res.status_code == 200


@pytest.mark.integration
async def test_company_duplicate_name_rejected(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    company_payload: Callable[..., dict[str, object]],
):
    await make_user()
    await create_company(name="Unique Company")

    res = await client.post(
        "/api/v1/companies/", json=company_payload(name="Unique Company")
    )
    assert res.status_code == 409
