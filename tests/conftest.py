import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable

import pytest
import pytest_asyncio
from bcrypt import gensalt, hashpw
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
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import create_token

settings = get_settings()


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
async def connection() -> AsyncGenerator[AsyncConnection]:
    async with engine.connect() as conn:
        tx = await conn.begin()

        try:
            yield conn
        finally:
            await tx.rollback()


@pytest.fixture
async def session(
    connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession]:
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
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    base_url = "http://localhost"
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=base_url,
        follow_redirects=False,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


def set_client_cookie(client: AsyncClient, name: str, value: str):
    client.cookies.set(
        name=name, value=value, domain="localhost.local", path="/"
    )


@pytest.fixture
async def make_user(
    client: AsyncClient, session: AsyncSession
) -> Callable[..., Awaitable[UserModel]]:
    async def _make_user(**kwargs) -> UserModel:
        hash_password: str | None = None

        if kwargs.pop("with_password", True):
            password_str = str(kwargs.pop("password_hash", "securepassword"))
            hash_password_bytes = await asyncio.to_thread(
                hashpw, password_str.encode(), gensalt(rounds=8)
            )
            hash_password = hash_password_bytes.decode()

        user = await UsersRepository.create(
            session,
            kwargs.pop("email", "user@example.com"),
            kwargs.pop("first_name", "Test"),
            kwargs.pop("last_name", "User"),
            hash_password,
        )

        if kwargs.get("with_oauth_user", False):
            await OAuthUsersRepository.create(
                session,
                provider_id="1234567890",
                user_id=user.id,
                provider=Provider.google,
            )

        if kwargs.get("with_session", True):
            cookies = {
                "access_token": create_token(user.id, "access"),
                "refresh_token": create_token(user.id, "refresh"),
            }

            await SessionsRepository.create(
                session,
                cookies["refresh_token"],
                user.id,
                user_agent="pytest",
                ip_addr="127.0.0.1",
                device_name="test",
            )

            set_client_cookie(client, "access_token", cookies["access_token"])
            set_client_cookie(client, "refresh_token", cookies["refresh_token"])

        await session.flush()

        return user

    return _make_user


@pytest.fixture
def mock_google_oauth():
    google_user = GoogleUser(
        sub="google",
        email="google@gmail.com",
        email_verified=True,
        given_name="Goo",
        family_name="Gle",
    )

    async def override_google_callback_dep():
        return google_user

    app.dependency_overrides[google_callback_dep] = override_google_callback_dep
    yield google_user
    app.dependency_overrides.pop(google_callback_dep, None)
