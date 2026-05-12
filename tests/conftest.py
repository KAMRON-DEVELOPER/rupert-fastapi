from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from src.apps.shared.models.base import Base
from src.core.database import get_session

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/rupert_test_db"

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
        yield s
