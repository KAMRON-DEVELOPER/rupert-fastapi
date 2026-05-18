from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_resume_skill_crud_and_duplicate_rejected(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    skill: SkillModel,
    resume_payload: Callable[..., dict[str, object]],
):
    await make_user()
    resume_res = await client.post(
        "/api/v1/users/resumes", json=resume_payload(title="Skill Resume")
    )
    resume_id = resume_res.json()["id"]

    create_res = await client.post(
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={"skillId": str(skill.id), "proficiency": "intermediate"},
    )
    assert create_res.status_code == 201
    skill_link_id = create_res.json()["id"]
    assert create_res.json()["skill"]["name"] == "Python"

    duplicate_res = await client.post(
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={"skillId": str(skill.id), "proficiency": "advanced"},
    )
    assert duplicate_res.status_code == 409

    patch_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}",
        json={"proficiency": "advanced", "lastUsedAt": "2025-01-01"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["proficiency"] == "advanced"
    assert patch_res.json()["lastUsedAt"] == "2025-01-01"

    delete_res = await client.delete(
        f"/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}"
    )
    assert delete_res.status_code == 200

    detail_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["skills"] == []


@pytest.mark.integration
async def test_resume_skill_rejects_modifying_another_users_resume(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    skill: SkillModel,
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    resume_payload: Callable[..., dict[str, object]],
):
    owner = await make_user(email="resume-skill-owner@example.com")
    resume_res = await client.post(
        "/api/v1/users/resumes",
        json=resume_payload(
            skills=[{"skillId": str(skill.id), "proficiency": "beginner"}]
        ),
    )
    resume_id = resume_res.json()["id"]
    skill_link_id = resume_res.json()["skills"][0]["id"]

    other = await make_user(
        email="resume-skill-other@example.com",
        first_name="Other",
        with_session=False,
    )
    await authenticate_as(client, session, other)

    create_res = await client.post(
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={"skillId": str(skill.id), "proficiency": "advanced"},
    )
    assert create_res.status_code == 404

    patch_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}",
        json={"proficiency": "advanced"},
    )
    assert patch_res.status_code == 404

    delete_res = await client.delete(
        f"/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}"
    )
    assert delete_res.status_code == 404

    await authenticate_as(client, session, owner)
    detail_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["skills"]) == 1
