from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_company_member_create_update_delete_and_duplicate_rejected(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
):
    await make_user(email="member-owner@example.com")
    user = await make_user(
        email="member-user@example.com", first_name="Member", with_session=False
    )
    company = await create_company(name="Member Company")

    create_res = await client.post(
        f"/api/v1/companies/{company['id']}/members",
        json={"userId": str(user.id), "role": "recruiter"},
    )
    assert create_res.status_code == 201
    member = create_res.json()
    assert member["companyId"] == company["id"]
    assert member["role"] == "recruiter"
    assert member["user"]["firstName"] == user.first_name

    duplicate_res = await client.post(
        f"/api/v1/companies/{company['id']}/members",
        json={"userId": str(user.id), "role": "member"},
    )
    assert duplicate_res.status_code == 409

    patch_res = await client.patch(
        f"/api/v1/companies/{company['id']}/members/{member['id']}",
        json={"role": "member"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["role"] == "member"

    delete_res = await client.delete(
        f"/api/v1/companies/{company['id']}/members/{member['id']}"
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["message"] == (
        "Company member deleted successfully"
    )

    missing_member_res = await client.patch(
        f"/api/v1/companies/{company['id']}/members/{member['id']}",
        json={"role": "recruiter"},
    )
    assert missing_member_res.status_code == 404


@pytest.mark.integration
async def test_company_member_routes_require_owner_permissions(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
):
    owner = await make_user(email="owner-permissions@example.com")
    recruiter = await make_user(
        email="recruiter-permissions@example.com",
        first_name="Recruiter",
        with_session=False,
    )
    candidate = await make_user(
        email="candidate-permissions@example.com",
        first_name="Candidate",
        with_session=False,
    )
    company = await create_company(name="Permissions Company")
    owner_member_id = company["members"][0]["id"]

    recruiter_res = await client.post(
        f"/api/v1/companies/{company['id']}/members",
        json={"userId": str(recruiter.id), "role": "recruiter"},
    )
    assert recruiter_res.status_code == 201

    self_role_res = await client.patch(
        f"/api/v1/companies/{company['id']}/members/{owner_member_id}",
        json={"role": "recruiter"},
    )
    assert self_role_res.status_code == 400

    self_delete_res = await client.delete(
        f"/api/v1/companies/{company['id']}/members/{owner_member_id}"
    )
    assert self_delete_res.status_code == 400

    await authenticate_as(client, session, recruiter)
    forbidden_add_res = await client.post(
        f"/api/v1/companies/{company['id']}/members",
        json={"userId": str(candidate.id), "role": "member"},
    )
    assert forbidden_add_res.status_code == 403

    await authenticate_as(client, session, owner)
    missing_company_res = await client.post(
        f"/api/v1/companies/{uuid4()}/members",
        json={"userId": str(candidate.id), "role": "member"},
    )
    assert missing_company_res.status_code == 404
