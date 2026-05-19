from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_resume_create_list_detail_update_and_delete(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    skill: SkillModel,
    another_skill: SkillModel,
    resume_payload: Callable[..., dict[str, object]],
):
    await make_user()

    empty_resume_res = await client.post(
        "/api/v1/users/resumes",
        json=resume_payload(title="Resume Without Skills"),
    )
    assert empty_resume_res.status_code == 201
    assert empty_resume_res.json()["skills"] == []

    create_res = await client.post(
        "/api/v1/users/resumes",
        json=resume_payload(
            skills=[{"skillId": str(skill.id), "proficiency": "intermediate"}],
        ),
    )
    assert create_res.status_code == 201
    created = create_res.json()
    resume_id = created["id"]
    assert created["skills"][0]["skill"]["name"] == "Python"

    list_res = await client.get("/api/v1/users/resumes")
    assert list_res.status_code == 200
    assert {item["id"] for item in list_res.json()} == {
        empty_resume_res.json()["id"],
        resume_id,
    }

    detail_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["skills"][0]["skill"]["name"] == "Python"

    patch_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}",
        json={"title": "Senior Backend Resume"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Senior Backend Resume"
    assert [item["skill"]["name"] for item in patch_res.json()["skills"]] == [
        "Python"
    ]

    replace_skills_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}",
        json={
            "skills": [
                {
                    "skillId": str(another_skill.id),
                    "proficiency": "advanced",
                    "lastUsedAt": "2025-01-01",
                }
            ]
        },
    )
    assert replace_skills_res.status_code == 200
    assert len(replace_skills_res.json()["skills"]) == 1
    assert replace_skills_res.json()["skills"][0]["skill"]["name"] == "FastAPI"
    assert replace_skills_res.json()["skills"][0]["proficiency"] == "advanced"

    delete_res = await client.delete(f"/api/v1/users/resumes/{resume_id}")
    assert delete_res.status_code == 200

    get_deleted_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert get_deleted_res.status_code == 404


@pytest.mark.integration
async def test_resume_rejects_invalid_salary_range(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    resume_payload: Callable[..., dict[str, object]],
):
    await make_user()

    res = await client.post(
        "/api/v1/users/resumes",
        json=resume_payload(
            salaryExpectationMin=5_000,
            salaryExpectationMax=4_000,
            salaryCurrency="USD",
        ),
    )
    assert res.status_code == 422


@pytest.mark.integration
async def test_resume_rejects_accessing_another_users_resume(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    resume_payload: Callable[..., dict[str, object]],
):
    owner = await make_user(email="resume-owner@example.com")
    create_res = await client.post(
        "/api/v1/users/resumes", json=resume_payload(title="Owner Resume")
    )
    resume_id = create_res.json()["id"]

    other = await make_user(
        email="resume-other@example.com",
        first_name="Other",
        with_session=False,
    )
    await authenticate_as(client, session, other)

    get_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert get_res.status_code == 404

    patch_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}", json={"title": "Nope"}
    )
    assert patch_res.status_code == 404

    delete_res = await client.delete(f"/api/v1/users/resumes/{resume_id}")
    assert delete_res.status_code == 404

    await authenticate_as(client, session, owner)
    owner_get_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert owner_get_res.status_code == 200
