from collections.abc import AsyncGenerator, Awaitable, Callable
from uuid import uuid4

import pytest
import pytest_asyncio
from dead_simple_oauth_fastapi import GoogleUser
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from main import app
from src.apps.shared.models.base import Base
from src.apps.shared.schemas.enums import Provider
from src.apps.users.models import UserModel
from src.apps.users.repositories.oauth_user import OAuthUsersRepository
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.core.database import get_session
from src.core.oauth import google_callback_dep
from src.dependencies.proactive_refresh import create_token

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:password@localhost:5432/rupert_test_db"
)

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def connection() -> AsyncGenerator[AsyncConnection, None]:
    async with engine.connect() as conn:
        tx = await conn.begin()

        try:
            yield conn
        finally:
            await tx.rollback()


@pytest.fixture
async def session(
    connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession, None]:
    session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    async with session() as s:
        yield s


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_google_oauth():
    async def override_google_callback_dep():
        return GoogleUser(
            sub="google",
            email="google@gmail.com",
            email_verified=True,
            given_name="Goo",
            family_name="Gle",
        )

    app.dependency_overrides[google_callback_dep] = override_google_callback_dep
    yield
    app.dependency_overrides.pop(google_callback_dep, None)


@pytest.fixture
async def authenticate_user(
    client: AsyncClient, session: AsyncSession
) -> Callable[..., Awaitable[UserModel]]:
    async def _authenticate_user(**kwargs) -> UserModel:
        password = (
            kwargs.pop("password_hash", "securepassword")
            if kwargs.pop("no_password", False)
            else None
        )
        user = await UsersRepository.create(
            kwargs.pop("email", "user@example.com"),
            password,
            kwargs.pop("first_name", "Test"),
            kwargs.pop("last_name", "User"),
            session,
        )
        if kwargs.get("with_oauth_user", False):
            await OAuthUsersRepository.create(
                session,
                provider_id=uuid4(),
                user_id=user.id,
                provider=Provider.google,
            )

        cookies = {
            "access_token": create_token(user.id, "access"),
            "refresh_token": create_token(user.id, "refresh"),
        }

        await SessionsRepository.create(
            user_id=user.id,
            user_agent="pytest",
            ip_addr="127.0.0.1",
            device_name="test",
            refresh_token=cookies["refresh_token"],
            session=session,
        )
        await session.flush()

        client.cookies.set("access_token", cookies["access_token"])
        client.cookies.set("refresh_token", cookies["refresh_token"])

        return user

    return _authenticate_user
