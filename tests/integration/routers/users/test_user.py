import io
from collections.abc import Awaitable, Callable
from typing import cast

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import UserModel
from src.apps.users.repositories.user import UsersRepository


@pytest.mark.integration
async def test_get_user_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/users/")
    assert res.status_code == 401


@pytest.mark.integration
async def test_get_user_authenticated(
    client: AsyncClient, make_user: Callable[..., Awaitable[UserModel]]
):
    user = await make_user()
    assert user is not None

    res = await client.get("/api/v1/users/")
    assert res.status_code == 200
    assert res.json()["email"] == user.email


def make_png_bytes(size=(128, 128)) -> bytes:
    image = Image.new("RGB", size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.integration
async def test_update_user_uploads_avatar(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    monkeypatch,
):
    user = await make_user()

    calls = []

    async def fake_put_object_to_boto3(
        object_name: str,
        data: bytes,
        content_type: str,
        old_object_name: str | None = None,
        for_update: bool = False,
    ):
        calls.append(
            {
                "object_name": object_name,
                "data": data,
                "content_type": content_type,
                "old_object_name": old_object_name,
                "for_update": for_update,
            }
        )

    monkeypatch.setattr(
        "src.apps.users.routes.user.put_object_to_boto3",
        fake_put_object_to_boto3,
    )

    avatar_bytes = make_png_bytes(size=(128, 128))

    res = await client.patch(
        "/api/v1/users/",
        files={
            "avatar": ("avatar.png", avatar_bytes, "image/png"),
        },
        data={
            "firstName": "Kamron",
            "lastName": "Atajanov",
            "headline": "Backend Developer",
            "birthdate": "2003-12-19",
            "bio": "Building with FastAPI",
            "specialization": "backend",
            "phoneNumber": "+998901234567",
            "githubUrl": "https://github.com/KAMRON-DEVELOPER",
            "telegramUsername": "lockdown2003",
            "follow_policy": "require_approval",
            "jobSearchStatus": "actively_looking",
        },
    )

    assert res.status_code in (200, 204)

    assert len(calls) == 1
    assert calls[0]["object_name"] == f"users/{user.id.hex}/avatar"
    assert calls[0]["data"] == avatar_bytes
    assert calls[0]["content_type"] == "image/png"

    updated_user = await UsersRepository.get_summary_by_id(session, user.id)
    updated_user = cast(UserModel, updated_user)
    assert updated_user.avatar_url == f"users/{user.id.hex}/avatar"
