from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_vacancy_skill_create_update_delete_and_duplicate_rejected(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
    skill: SkillModel,
):
    await make_user()
    company = await create_company(name="Skill Company")
    vacancy = await create_vacancy(company["id"], title="Skill Vacancy")

    create_res = await client.post(
        f"/api/v1/vacancies/{vacancy['id']}/skills",
        json={
            "skillId": str(skill.id),
            "proficiency": "intermediate",
            "yearsOfExperienceMin": 1,
            "isRequired": True,
        },
    )
    assert create_res.status_code == 201
    link = create_res.json()
    assert link["vacancyId"] == vacancy["id"]
    assert link["skill"]["name"] == "Python"

    duplicate_res = await client.post(
        f"/api/v1/vacancies/{vacancy['id']}/skills",
        json={"skillId": str(skill.id), "proficiency": "advanced"},
    )
    assert duplicate_res.status_code == 409

    patch_res = await client.patch(
        f"/api/v1/vacancies/{vacancy['id']}/skills/{link['id']}",
        json={
            "proficiency": "expert",
            "yearsOfExperienceMin": 3,
            "isRequired": False,
        },
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["proficiency"] == "expert"
    assert patch_res.json()["yearsOfExperienceMin"] == 3.0
    assert patch_res.json()["isRequired"] is False

    delete_res = await client.delete(
        f"/api/v1/vacancies/{vacancy['id']}/skills/{link['id']}"
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["message"] == "Vacancy skill deleted successfully"

    missing_link_res = await client.delete(
        f"/api/v1/vacancies/{vacancy['id']}/skills/{link['id']}"
    )
    assert missing_link_res.status_code == 404


@pytest.mark.integration
async def test_vacancy_skill_routes_require_company_member_permissions(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    create_company: Callable[..., Awaitable[dict[str, Any]]],
    create_vacancy: Callable[..., Awaitable[dict[str, Any]]],
    skill: SkillModel,
):
    owner = await make_user(email="skill-owner@example.com")
    company = await create_company(name="Skill Permissions Company")
    vacancy = await create_vacancy(company["id"], title="Skill Permissions")
    link_res = await client.post(
        f"/api/v1/vacancies/{vacancy['id']}/skills",
        json={"skillId": str(skill.id), "proficiency": "advanced"},
    )
    assert link_res.status_code == 201

    other = await make_user(
        email="skill-other@example.com",
        first_name="Other",
        with_session=False,
    )
    await authenticate_as(client, session, other)

    create_res = await client.post(
        f"/api/v1/vacancies/{vacancy['id']}/skills",
        json={"skillId": str(skill.id), "proficiency": "expert"},
    )
    assert create_res.status_code == 403

    patch_res = await client.patch(
        f"/api/v1/vacancies/{vacancy['id']}/skills/{link_res.json()['id']}",
        json={"proficiency": "expert"},
    )
    assert patch_res.status_code == 403

    await authenticate_as(client, session, owner)
    missing_vacancy_res = await client.post(
        f"/api/v1/vacancies/{uuid4()}/skills",
        json={"skillId": str(skill.id), "proficiency": "expert"},
    )
    assert missing_vacancy_res.status_code == 404
