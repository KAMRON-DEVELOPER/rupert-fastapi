from collections.abc import Awaitable, Callable
from uuid import uuid4

import pytest
from dead_simple_oauth_fastapi import GoogleUser
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import OAuthUserModel, SessionModel, UserModel
from src.core.oauth import google
from src.dependencies.proactive_refresh import create_token


@pytest.mark.integration
async def test_google_oauth_redirect(client: AsyncClient, monkeypatch):
    async def fake_redirect(_req):
        return RedirectResponse("https://provider.test/oauth")

    monkeypatch.setattr(google, "redirect", fake_redirect)

    res = await client.get("/api/v1/users/auth/google")

    assert res.status_code == 307
    assert res.headers["location"] == "https://provider.test/oauth"


@pytest.mark.integration
async def test_google_oauth_callback_creates_user(
    client: AsyncClient, session: AsyncSession, mock_google_oauth: GoogleUser
):
    res = await client.get("/api/v1/users/auth/google/callback", params={})
    assert res.status_code == 307

    user = await session.scalar(
        select(UserModel).where(UserModel.email == mock_google_oauth.email)
    )
    assert user is not None
    assert user.email_verified is True

    oauth_user = await session.scalar(
        select(OAuthUserModel).where(
            OAuthUserModel.provider_id == mock_google_oauth.sub
        )
    )
    assert oauth_user is not None

    user_session = await session.scalar(
        select(SessionModel).where(SessionModel.user_id == user.id)
    )
    assert user_session is not None

    assert "access_token" in client.cookies
    assert "refresh_token" in client.cookies


@pytest.mark.integration
async def test_password_setup_valid_token(
    client: AsyncClient, make_user: Callable[..., Awaitable[UserModel]]
):
    user = await make_user()
    assert user is not None

    token = create_token(user.id, "password_setup")
    res = await client.post(
        "/api/v1/users/auth/password-setup",
        json={"password": "supersecret"},
        params={"token": token},
    )
    assert res.status_code == 307
    assert "auth" in res.headers["location"]


@pytest.mark.integration
async def test_password_setup_valid_token_no_user(client: AsyncClient):
    token = create_token(uuid4(), "password_setup")
    res = await client.post(
        "/api/v1/users/auth/password-setup",
        json={"password": "supersecret"},
        params={"token": token},
    )
    assert res.status_code == 400


@pytest.mark.integration
async def test_password_setup_invalid_token(client):
    res = await client.post(
        "/api/v1/users/auth/password-setup",
        json={"password": "supersecret"},
        params={"token": "bad"},
    )
    assert res.status_code == 401
