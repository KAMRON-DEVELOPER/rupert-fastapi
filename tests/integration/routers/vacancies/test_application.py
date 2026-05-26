from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_application_create_list_detail_update_and_duplicate_rejected(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
):
    owner = await make_user(email="application-owner@example.com")
    owner_id = owner.id
    company = await create_company(name="Application Company")
    vacancy = await create_vacancy(
        company["id"], title="Application Vacancy", status="open"
    )

    applicant = await make_user(
        email="applicant@example.com",
        first_name="Applicant",
        with_session=False,
    )
    await authenticate_as(client, session, applicant)

    create_res = await client.post(
        "/api/v1/vacancies/applications",
        json={
            "vacancyId": vacancy["id"],
            "coverLetter": "I can build this service.",
        },
    )
    assert create_res.status_code == 201
    application = create_res.json()
    assert application["vacancyId"] == vacancy["id"]
    assert application["applicantId"] == str(applicant.id)
    assert application["status"] == "pending"
    assert application["applicant"]["firstName"] == applicant.first_name

    duplicate_res = await client.post(
        "/api/v1/vacancies/applications", json={"vacancyId": vacancy["id"]}
    )
    assert duplicate_res.status_code == 409

    detail_res = await client.get(
        f"/api/v1/vacancies/applications/{application['id']}"
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["vacancy"]["title"] == "Application Vacancy"

    list_res = await client.get(
        "/api/v1/vacancies/applications",
        params={"applicantId": str(applicant.id), "status": "pending"},
    )
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["data"][0]["id"] == application["id"]

    vacancy_detail_res = await client.get(f"/api/v1/vacancies/{vacancy['id']}")
    assert vacancy_detail_res.status_code == 200
    assert vacancy_detail_res.json()["hasApplied"] is True

    owner = await session.get(UserModel, owner_id)
    assert owner is not None
    await authenticate_as(client, session, owner)
    patch_res = await client.patch(
        f"/api/v1/vacancies/applications/{application['id']}",
        json={"status": "shortlisted", "recruiterNote": "Strong profile"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "shortlisted"
    assert patch_res.json()["recruiterNote"] == "Strong profile"


@pytest.mark.integration
async def test_application_precondition_permission_and_missing_paths(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
):
    owner = await make_user(email="application-precondition-owner@example.com")
    company = await create_company(name="Application Precondition Company")
    draft_vacancy = await create_vacancy(
        company["id"], title="Draft Vacancy", status="draft"
    )
    open_vacancy = await create_vacancy(
        company["id"], title="Open Vacancy", status="open"
    )

    applicant = await make_user(
        email="precondition-applicant@example.com",
        first_name="Applicant",
        with_session=False,
    )
    await authenticate_as(client, session, applicant)

    closed_apply_res = await client.post(
        "/api/v1/vacancies/applications",
        json={"vacancyId": draft_vacancy["id"]},
    )
    assert closed_apply_res.status_code == 400

    application_res = await client.post(
        "/api/v1/vacancies/applications", json={"vacancyId": open_vacancy["id"]}
    )
    assert application_res.status_code == 201

    patch_forbidden_res = await client.patch(
        f"/api/v1/vacancies/applications/{application_res.json()['id']}",
        json={"status": "viewed"},
    )
    assert patch_forbidden_res.status_code == 403

    await authenticate_as(client, session, owner)
    missing_id = uuid4()

    detail_missing_res = await client.get(
        f"/api/v1/vacancies/applications/{missing_id}"
    )
    assert detail_missing_res.status_code == 404

    patch_missing_res = await client.patch(
        f"/api/v1/vacancies/applications/{missing_id}",
        json={"status": "viewed"},
    )
    assert patch_missing_res.status_code == 404


@pytest.mark.integration
async def test_apply_to_vacancy_requires_auth(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
):
    await make_user()
    company = await create_company(name="Application Auth Company")
    vacancy = await create_vacancy(company["id"], title="Application Auth")
    client.cookies.clear()

    res = await client.post(
        "/api/v1/vacancies/applications", json={"vacancyId": vacancy["id"]}
    )
    assert res.status_code == 401
