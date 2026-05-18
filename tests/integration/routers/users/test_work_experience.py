from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_work_experience_crud(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
):
    await make_user()

    create_res = await client.post(
        "/api/v1/users/work-experiences",
        json={
            "companyName": "Acme",
            "position": "Backend Engineer",
            "startedAt": "2024-01-01",
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()
    work_experience_id = created["id"]
    assert created["companyName"] == "Acme"
    assert created["isCurrent"] is True

    list_res = await client.get("/api/v1/users/work-experiences")
    assert list_res.status_code == 200
    assert [item["id"] for item in list_res.json()] == [work_experience_id]

    patch_res = await client.patch(
        f"/api/v1/users/work-experiences/{work_experience_id}",
        json={"location": "Remote", "endedAt": "2025-01-01"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["location"] == "Remote"
    assert patch_res.json()["isCurrent"] is False

    delete_res = await client.delete(
        f"/api/v1/users/work-experiences/{work_experience_id}"
    )
    assert delete_res.status_code == 200

    list_after_delete_res = await client.get("/api/v1/users/work-experiences")
    assert list_after_delete_res.status_code == 200
    assert list_after_delete_res.json() == []


@pytest.mark.integration
async def test_work_experience_rejects_invalid_date_range(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
):
    await make_user()

    res = await client.post(
        "/api/v1/users/work-experiences",
        json={
            "companyName": "Acme",
            "position": "Backend Engineer",
            "startedAt": "2024-01-01",
            "endedAt": "2023-12-31",
        },
    )
    assert res.status_code == 422


@pytest.mark.integration
async def test_work_experience_rejects_updating_and_deleting_another_users_item(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
):
    owner = await make_user(email="owner@example.com")
    create_res = await client.post(
        "/api/v1/users/work-experiences",
        json={
            "companyName": "Owner Co",
            "position": "Engineer",
            "startedAt": "2024-01-01",
        },
    )
    work_experience_id = create_res.json()["id"]

    other = await make_user(
        email="other@example.com", first_name="Other", with_session=False
    )
    await authenticate_as(client, session, other)

    patch_res = await client.patch(
        f"/api/v1/users/work-experiences/{work_experience_id}",
        json={"location": "Remote"},
    )
    assert patch_res.status_code == 404

    delete_res = await client.delete(
        f"/api/v1/users/work-experiences/{work_experience_id}"
    )
    assert delete_res.status_code == 404

    await authenticate_as(client, session, owner)
    list_res = await client.get("/api/v1/users/work-experiences")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
