from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import UserModel
from src.apps.users.repositories.user import UsersRepository
from src.dependencies.proactive_refresh import create_token
from src.services.mailtrap import Mailtrap


@pytest.mark.integration
async def test_email_auth_new_user(client: AsyncClient):
    """New user"""
    payload = {"email": "user@example.com", "password": "securepassword"}

    res = await client.post("/api/v1/users/auth/email", json=payload)

    assert res.status_code == 200
    assert res.json()["message"] == "new_user"


@pytest.mark.integration
async def test_email_auth_create_user(
    client: AsyncClient, session: AsyncSession, monkeypatch
):
    "Create user"
    sent = {}

    async def fake_send_email_verification_link(
        _cls, to_name: str, to_email: str, link: str, _cfg
    ):
        sent["to_name"] = to_name
        sent["to_email"] = to_email
        sent["link"] = link

    monkeypatch.setattr(
        Mailtrap,
        "send_email_verification_link",
        classmethod(fake_send_email_verification_link),
    )

    payload = {
        "email": "user@example.com",
        "password": "securepassword",
        "firstName": "Test",
        "lastName": "User",
    }
    res = await client.post("/api/v1/users/auth/email", json=payload)

    assert res.status_code == 200

    user = await UsersRepository.find_by_email("user@example.com", session)
    assert user is not None
    assert user.first_name == "Test"

    assert sent["to_email"] == "user@example.com"
    assert "/auth/verify?token=" in sent["link"]


@pytest.mark.integration
async def test_email_auth_correct_password(
    client: AsyncClient,
    authenticate_user: Callable[..., Awaitable[UserModel]],
):
    """User exist, correct password"""
    user = await authenticate_user()
    assert user is not None

    payload = {"email": "user@example.com", "password": "securepassword"}
    res = await client.post("/api/v1/users/auth/email", json=payload)

    assert res.status_code == 200
    assert res.json()["firstName"] == user.first_name


@pytest.mark.integration
async def test_email_auth_incorrect_password(
    client: AsyncClient,
    authenticate_user: Callable[..., Awaitable[UserModel]],
):
    """User exist, incorrect password"""
    user = await authenticate_user()
    assert user is not None

    payload = {"email": "user@example.com", "password": "incorrectpassword"}
    res = await client.post("/api/v1/users/auth/email", json=payload)

    assert res.status_code == 400
    assert res.json()["details"] == "password is not match."


@pytest.mark.integration
async def test_email_auth_password_not_set(
    client: AsyncClient,
    authenticate_user: Callable[..., Awaitable[UserModel]],
    monkeypatch,
):
    """Password not set"""
    sent = {}

    async def fake_send_password_setup_link(
        _cls, to_name: str, to_email: str, link: str, _cfg
    ):
        sent["to_name"] = to_name
        sent["to_email"] = to_email
        sent["link"] = link

    monkeypatch.setattr(
        Mailtrap,
        "send_password_setup_link",
        classmethod(fake_send_password_setup_link),
    )

    user = await authenticate_user(no_password=False, with_oauth_user=True)
    assert user is not None

    payload = {"email": "user@example.com", "password": "anypassword"}
    res = await client.post("/api/v1/users/auth/email", json=payload)

    assert res.status_code == 200
    assert sent["to_email"] == user.email
    assert "/auth/set-password?token=" in sent["link"]
    assert "message" in res.json()


@pytest.mark.integration
async def test_email_auth_password_not_set_no_providers(
    client: AsyncClient,
    authenticate_user: Callable[..., Awaitable[UserModel]],
):
    """Password not set, no providers"""
    user = await authenticate_user(no_password=False)
    assert user is not None

    payload = {"email": "user@example.com", "password": "anypassword"}
    res = await client.post("/api/v1/users/auth/email", json=payload)

    assert res.status_code == 500
    assert "detail" in res.json()


@pytest.mark.integration
async def test_verify_email_message_response(
    client: AsyncClient,
    session: AsyncSession,
    authenticate_user: Callable[..., Awaitable[UserModel]],
):
    "Verify email message response"
    user = await authenticate_user()
    assert user is not None

    token = create_token(user.id, "email_verification")

    res = await client.post(
        "/api/v1/users/auth/verify", params={"token": token}
    )
    assert res.status_code == 200
    assert "message" in res.json()

    user = await UsersRepository.get_by_id(user.id, session)
    assert user.email_verified


@pytest.mark.integration
async def test_logout_requires_auth(client: AsyncClient):
    "Logout, unauthenticated"
    res = await client.post("/api/v1/users/auth/logout")

    assert res.status_code == 401


@pytest.mark.integration
async def test_logout_delete_session_delete_cookies(
    client: AsyncClient,
    authenticate_user: Callable[..., Awaitable[UserModel]],
):
    "Logout, delete session, delete cookies"
    user = await authenticate_user(with_session=True)
    assert user is not None

    refresh_token = client.cookies.get("refresh_token")
    assert refresh_token is not None

    res = await client.post("/api/v1/users/auth/logout")
    set_cookie_headers = res.headers.get_list("set-cookie")
    assert res.status_code == 200
    assert "message" in res.json()

    access_delete_headers = [
        h for h in set_cookie_headers if h.startswith("access_token=")
    ]
    refresh_delete_headers = [
        h for h in set_cookie_headers if h.startswith("refresh_token=")
    ]

    assert access_delete_headers
    assert refresh_delete_headers

    assert any(
        "Max-Age=0" in h or "max-age=0" in h.lower()
        for h in access_delete_headers
    )
    assert any(
        "Max-Age=0" in h or "max-age=0" in h.lower()
        for h in refresh_delete_headers
    )

    assert "access_token" not in client.cookies
    assert "refresh_token" not in client.cookies
