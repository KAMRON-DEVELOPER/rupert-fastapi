from collections.abc import AsyncGenerator, Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from src.apps.shared.models.base import Base
from src.apps.users.models import UserModel
from src.apps.users.repositories.session import SessionsRepository
from src.core.database import get_session
from src.dependencies.proactive_refresh import create_token

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@192.168.10.11:5432/rupert_test_db"

async_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as s:
        yield s


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
async def setup_db():
    """
    Creates fresh tables before each test and drops them after.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """
    Provides an async HTTP client to make requests to the FastAPI app.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def session():
    """
    Provides a direct database session for tests to arrange data or assert DB state.
    """
    async with async_session() as s:
        try:
            yield s
        finally:
            await s.rollback()


@pytest.fixture
async def make_user(session: AsyncSession) -> Callable[..., Awaitable[UserModel]]:
    async def _make_user(**kwargs) -> UserModel:
        payload = {
            "email": kwargs.pop("email", "user@example.com"),
            "password_hash": kwargs.pop("password_hash", "hash"),
            "first_name": kwargs.pop("first_name", "Test"),
            "last_name": kwargs.pop("last_name", "User"),
        }
        user = UserModel(**payload, **kwargs)
        session.add(user)
        await session.flush()
        return user

    return _make_user


@pytest.fixture
async def auth_cookies() -> Callable[[UserModel], dict[str, str]]:
    def _auth_cookies(user: UserModel) -> dict[str, str]:
        return {
            "access_token": create_token(user.id, "access"),
            "refresh_token": create_token(user.id, "refresh"),
        }

    return _auth_cookies


@pytest.fixture
async def login_client(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    auth_cookies: Callable[[UserModel], dict[str, str]],
):
    async def _login(**kwargs):
        user = await make_user(**kwargs)
        cookies = auth_cookies(user)
        await SessionsRepository.create(
            user_id=user.id,
            user_agent="pytest",
            ip_addr="127.0.0.1",
            device_name="test",
            refresh_token=cookies["refresh_token"],
            session=session,
        )
        await session.commit()

        client.cookies.set("access_token", cookies["access_token"])
        client.cookies.set("refresh_token", cookies["refresh_token"])
        return user

    return _login
