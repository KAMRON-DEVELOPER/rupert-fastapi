import pytest
from httpx import AsyncClient

from src.dependencies.proactive_refresh import create_token


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
