from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.routing import APIRoute

from main import app
from src.apps.users.models import UserModel


def _callback_dep(path: str) -> Any:
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path:
            return route.dependant.dependencies[0].call
    raise AssertionError("dependency not found")


@pytest.mark.asyncio
async def test_google_callback_with_override(client, session):
    dep = _callback_dep("/api/v1/users/auth/google/callback")

    async def fake_google_user():
        return SimpleNamespace(email="g@example.com", email_verified=True, given_name="G", family_name="User")

    app.dependency_overrides[dep] = fake_google_user
    try:
        res = await client.get("/api/v1/users/auth/google/callback")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 307
    assert (await session.execute(UserModel.__table__.select())).first() is not None


@pytest.mark.asyncio
async def test_github_callback_with_override(client):
    dep = _callback_dep("/api/v1/users/auth/github/callback")

    async def fake_github_user():
        return SimpleNamespace(email="gh@example.com", name="GH User")

    app.dependency_overrides[dep] = fake_github_user
    try:
        res = await client.get("/api/v1/users/auth/github/callback")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 307


@pytest.mark.asyncio
async def test_password_setup_invalid_token(client):
    res = await client.post("/api/v1/users/auth/password-setup?token=bad", json={"password": "secret123"})
    assert res.status_code == 401
