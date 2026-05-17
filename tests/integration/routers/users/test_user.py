from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient

from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_get_user_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/users/")
    assert res.status_code == 401


@pytest.mark.integration
async def test_get_user_authenticated(
    client: AsyncClient, authenticate_user: Callable[..., Awaitable[UserModel]]
):
    user = await authenticate_user()
    assert user is not None

    res = await client.get("/api/v1/users/")

    assert res.status_code == 200
    assert res.json()["email"] == user.email
