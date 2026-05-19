from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_user_skill_crud_list_and_duplicate_rejected(
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

    list_res = await client.get("/api/v1/users/skills")
    assert list_res.status_code == 200
    assert [item["id"] for item in list_res.json()] == [link_id]

    duplicate_res = await client.post(
        "/api/v1/users/skills",
        json={"skillId": str(skill.id), "proficiency": "advanced"},
    )
    assert duplicate_res.status_code == 409

    patch_res = await client.patch(
        f"/api/v1/users/skills/{link_id}",
        json={"proficiency": "expert", "lastUsedAt": "2025-01-01"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["proficiency"] == "expert"
    assert patch_res.json()["lastUsedAt"] == "2025-01-01"

    delete_res = await client.delete(f"/api/v1/users/skills/{link_id}")
    assert delete_res.status_code == 200
