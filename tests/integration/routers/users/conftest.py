from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.apps.users.models import UserModel
from src.apps.users.repositories.session import SessionsRepository
from src.dependencies.proactive_refresh import create_token
from tests.conftest import set_client_cookie


async def _authenticate_as(
    client: AsyncClient, session: AsyncSession, user: UserModel
) -> str:
    access_token = create_token(user.id, "access")
    refresh_token = create_token(user.id, "refresh")

    await SessionsRepository.create(
        session,
        refresh_token,
        user.id,
        user_agent="pytest",
        ip_addr="127.0.0.1",
        device_name="test",
    )
    await session.flush()

    set_client_cookie(client, "access_token", access_token)
    set_client_cookie(client, "refresh_token", refresh_token)

    return refresh_token


async def _create_skill(session: AsyncSession, name: str) -> SkillModel:
    record = SkillModel(name=name)

    session.add(record)
    await session.flush()

    return record


def _resume_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Backend Resume",
        "specialization": "backend",
        "country": "UZ",
        "city": "Tashkent",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def authenticate_as() -> (
    Callable[[AsyncClient, AsyncSession, UserModel], Awaitable[str]]
):
    return _authenticate_as


@pytest.fixture
def resume_payload() -> Callable[..., dict[str, object]]:
    return _resume_payload


@pytest.fixture
async def skill(session: AsyncSession) -> SkillModel:
    return await _create_skill(session, "Python")


@pytest.fixture
async def another_skill(session: AsyncSession) -> SkillModel:
    return await _create_skill(session, "FastAPI")
