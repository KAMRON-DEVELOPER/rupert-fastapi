from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_resume_skill_batch_crud_and_duplicate_rejected(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    skill: SkillModel,
    another_skill: SkillModel,
    resume_payload: Callable[..., dict[str, object]],
):
    await make_user()
    resume_res = await client.post(
        "/api/v1/users/resumes", json=resume_payload(title="Skill Resume")
    )
    resume_id = resume_res.json()["id"]

    create_res = await client.post(
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={
            "skills": [
                {"skillId": str(skill.id), "proficiency": "intermediate"},
            ]
        },
    )
    assert create_res.status_code == 201
    assert len(create_res.json()) == 1
    assert create_res.json()[0]["skill"]["name"] == "Python"
    skill_link_id = create_res.json()[0]["id"]

    duplicate_res = await client.post(
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={
            "skills": [
                {"skillId": str(skill.id), "proficiency": "advanced"},
            ]
        },
    )
    assert duplicate_res.status_code == 409

    update_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={
            "skills": [
                {
                    "id": skill_link_id,
                    "skillId": str(skill.id),
                    "proficiency": "advanced",
                    "lastUsedAt": "2025-01-01",
                },
                {
                    "skillId": str(another_skill.id),
                    "proficiency": "beginner",
                },
            ]
        },
    )
    assert update_res.status_code == 200
    assert len(update_res.json()) == 2

    updated_skill = next(
        s for s in update_res.json() if s["id"] == skill_link_id
    )
    assert updated_skill["proficiency"] == "advanced"
    assert updated_skill["lastUsedAt"] == "2025-01-01"

    new_skill = next(
        s for s in update_res.json() if s["id"] != skill_link_id
    )
    assert new_skill["skill"]["name"] == "FastAPI"
    assert new_skill["proficiency"] == "beginner"

    delete_res = await client.request(
        "DELETE",
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={
            "skillLinkIds": [
                s["id"] for s in update_res.json()
            ]
        },
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
        json={
            "skills": [
                {"skillId": str(skill.id), "proficiency": "advanced"},
            ]
        },
    )
    assert create_res.status_code == 404

    update_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={
            "skills": [
                {
                    "id": skill_link_id,
                    "skillId": str(skill.id),
                    "proficiency": "advanced",
                },
            ]
        },
    )
    assert update_res.status_code == 404

    delete_res = await client.request(
        "DELETE",
        f"/api/v1/users/resumes/{resume_id}/skills",
        json={"skillLinkIds": [skill_link_id]},
    )
    assert delete_res.status_code == 404

    await authenticate_as(client, session, owner)
    detail_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["skills"]) == 1
