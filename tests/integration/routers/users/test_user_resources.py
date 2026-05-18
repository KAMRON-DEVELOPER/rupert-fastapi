from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.shared.schemas.enums import FollowPolicy
from src.apps.users.models import SessionModel, UserModel
from src.apps.users.repositories.follow import FollowsRepository
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository


@pytest.fixture
async def skill(session: AsyncSession) -> SkillModel:
    record = SkillModel(name="Python")
    session.add(record)
    await session.flush()
    return record


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
    work_experience_id = create_res.json()["id"]

    list_res = await client.get("/api/v1/users/work-experiences")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    patch_res = await client.patch(
        f"/api/v1/users/work-experiences/{work_experience_id}",
        json={"location": "Remote"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["location"] == "Remote"

    delete_res = await client.delete(
        f"/api/v1/users/work-experiences/{work_experience_id}"
    )
    assert delete_res.status_code == 200


@pytest.mark.integration
async def test_user_skill_crud_and_duplicate_rejected(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    skill: SkillModel,
):
    await make_user()

    create_res = await client.post(
        "/api/v1/users/skills",
        json={"skillId": str(skill.id), "proficiency": "advanced"},
    )
    assert create_res.status_code == 201
    link_id = create_res.json()["id"]
    assert create_res.json()["skill"]["name"] == "Python"

    duplicate_res = await client.post(
        "/api/v1/users/skills",
        json={"skillId": str(skill.id), "proficiency": "advanced"},
    )
    assert duplicate_res.status_code == 409

    patch_res = await client.patch(
        f"/api/v1/users/skills/{link_id}",
        json={"proficiency": "expert"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["proficiency"] == "expert"

    delete_res = await client.delete(f"/api/v1/users/skills/{link_id}")
    assert delete_res.status_code == 200


@pytest.mark.integration
async def test_resume_crud_and_granular_skill_management(
    client: AsyncClient,
    make_user: Callable[..., Awaitable[UserModel]],
    skill: SkillModel,
):
    await make_user()

    create_res = await client.post(
        "/api/v1/users/resumes",
        json={
            "title": "Backend Resume",
            "specialization": "backend",
            "country": "UZ",
            "city": "Tashkent",
            "skills": [
                {"skillId": str(skill.id), "proficiency": "intermediate"}
            ],
        },
    )
    assert create_res.status_code == 201
    resume_id = create_res.json()["id"]
    skill_link_id = create_res.json()["skills"][0]["id"]

    detail_res = await client.get(f"/api/v1/users/resumes/{resume_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["skills"][0]["skill"]["name"] == "Python"

    patch_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}",
        json={"title": "Senior Backend Resume"},
    )
    assert patch_res.status_code == 200
    assert len(patch_res.json()["skills"]) == 1

    skill_patch_res = await client.patch(
        f"/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}",
        json={"proficiency": "advanced"},
    )
    assert skill_patch_res.status_code == 200
    assert skill_patch_res.json()["proficiency"] == "advanced"

    skill_delete_res = await client.delete(
        f"/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}"
    )
    assert skill_delete_res.status_code == 200

    delete_res = await client.delete(f"/api/v1/users/resumes/{resume_id}")
    assert delete_res.status_code == 200


@pytest.mark.integration
async def test_follow_requests_and_lists(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    current = await make_user(email="current@example.com", first_name="Current")
    follower = await make_user(
        email="follower@example.com",
        first_name="Follower",
        with_session=False,
    )
    await UsersRepository.update(
        session, current.id, {"follow_policy": FollowPolicy.require_approval}
    )

    follow = await FollowsRepository.follow(session, follower.id, current.id)
    await session.flush()
    assert follow is not None

    requests_res = await client.get("/api/v1/users/follow-requests")
    assert requests_res.status_code == 200
    assert requests_res.json()["total"] == 1

    patch_res = await client.patch(
        f"/api/v1/users/follow-requests/{follow.id}",
        json={"status": "accepted"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "accepted"

    followers_res = await client.get("/api/v1/users/followers")
    assert followers_res.status_code == 200
    assert followers_res.json()["total"] == 1


@pytest.mark.integration
async def test_session_listing_and_revocation(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    user = await make_user()
    await SessionsRepository.create(
        session,
        "other-refresh-token",
        user.id,
        user_agent="pytest-2",
        ip_addr="127.0.0.2",
        device_name="other",
    )
    await session.flush()

    list_res = await client.get("/api/v1/users/sessions")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2
    assert "refreshToken" not in list_res.json()[0]

    revoke_res = await client.delete("/api/v1/users/sessions")
    assert revoke_res.status_code == 200

    remaining_sessions = (
        await session.scalars(
            select(SessionModel).where(SessionModel.user_id == user.id)
        )
    ).all()
    assert len(remaining_sessions) == 1
