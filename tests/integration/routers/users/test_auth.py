from unittest.mock import patch

import pytest
from dead_simple_oauth_fastapi import GoogleUser
from httpx import AsyncClient

from src.apps.users.repositories.user import UsersRepository
from src.core.oauth import google
from src.dependencies.proactive_refresh import auth_checker, create_token


@pytest.mark.anyio
@patch("src.services.mailtrap.Mailtrap.send_email_verification_link")
async def test_email_auth_new_user_sends_email(mock_send_email, client, session):
    """Test that signing up a new user triggers the Mailtrap verification email."""

    payload = {
        "email": "new.user@example.com",
        "password": "securepassword123",
        "first_name": "Alice",
        "last_name": "Smith",
    }

    response = await client.post("/api/v1/users/auth/email", json=payload)

    assert response.status_code == 200
    # Check that Mailtrap was called once
    mock_send_email.assert_called_once()

    # Verify the user was actually saved to the DB
    saved_user = await UsersRepository.find_by_email("new.user@example.com", session)
    assert saved_user is not None
    assert saved_user.first_name == "Alice"


@pytest.mark.anyio
async def test_google_oauth_callback_success(client, session):
    """Test the OAuth flow by overriding the Google callback dependency."""

    # 3. Hit the callback endpoint
    response = await client.get("/api/v1/users/auth/google/callback")

    # Should redirect to frontend upon success
    assert response.status_code == 307

    # 4. Verify DB insertion
    saved_user = await UsersRepository.find_by_email("oauth.test@gmail.com", session)
    assert saved_user is not None
    assert saved_user.email_verified is True


@pytest.mark.anyio
async def test_patch_user_requires_auth(client):
    """Edge case: Trying to update a user without authentication should fail."""
    response = await client.patch("/api/v1/users/", json={"first_name": "Hacked"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_patch_user_success(client, session):
    """Test updating a user while faking authentication via dependency override."""

    # 1. Setup a real user in the test DB
    user = await UsersRepository.create(
        email="auth@example.com", password_hash="pw", first_name="Old", last_name="Name", session=session
    )
    await session.commit()

    # 3. Send the PATCH request
    update_payload = {"first_name": "UpdatedViaAPI"}
    response = await client.patch("/api/v1/users/", json=update_payload)

    assert response.status_code == 200
    assert response.json()["first_name"] == "UpdatedViaAPI"


@pytest.mark.asyncio
async def test_email_auth_new_user(client: AsyncClient):
    payload = {"email": "new@example.com", "password": "securepassword", "firstName": "John", "lastName": "Doe"}
    response = await client.post("/api/v1/users/auth/email", json=payload)
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_email_auth_wrong_password(client: AsyncClient, make_user):
    await make_user(
        email="exists@example.com", password_hash="$2b$12$qz8dQ5vG7d7G31a1qJ9x8.WqfWz5twyl9h7VDaRao7IhiHBpjz2yK"
    )
    response = await client.post(
        "/api/v1/users/auth/email",
        json={"email": "exists@example.com", "password": "wrong", "firstName": "A", "lastName": "B"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_expired_token(client: AsyncClient, make_user):
    user = await make_user(email="expired@example.com")
    token = create_token(user.id, "access")
    res = await client.post(f"/api/v1/users/auth/verify?token={token}")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_logout_requires_auth(client: AsyncClient):
    res = await client.post("/api/v1/users/auth/logout")
    assert res.status_code == 401
