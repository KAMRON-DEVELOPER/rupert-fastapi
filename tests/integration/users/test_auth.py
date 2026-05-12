from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import UserModel


async def test_email_auth(client: AsyncClient, session: AsyncSession):
    payload = {"email": "test@example.com", "password": "securepassword", "firstName": "John", "lastName": "Doe"}

    response = await client.post("/api/v1/users/auth/email", json=payload)

    assert response.status_code == 200
    data: dict = response.json()

    assert "id" in data
    assert data.get("email") == "test@example.com"
    assert data.get("firstName") == "John"

    stmt = select(UserModel).where(UserModel.email == "test@example.com")
    result = await session.execute(stmt)
    user_in_db = result.scalar_one_or_none()

    assert user_in_db is not None
    assert user_in_db.first_name == "John"
    assert user_in_db.email_verified is False
