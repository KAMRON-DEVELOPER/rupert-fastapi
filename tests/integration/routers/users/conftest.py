from collections.abc import Awaitable, Callable
from typing import Any, cast

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


def _resume_payload(
    default_location: dict[str, object], **overrides: object
) -> dict[str, object]:
    country = cast(Any, default_location["country"])
    cities = cast(dict[str, Any], default_location["cities"])
    city_name = str(overrides.pop("city", "Tashkent"))
    overrides.pop("country", None)

    payload: dict[str, object] = {
        "title": "Backend Resume",
        "specialization": "backend",
        "countryId": str(country.id),
        "cityId": str(cities[city_name].id),
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def authenticate_as() -> Callable[
    [AsyncClient, AsyncSession, UserModel], Awaitable[str]
]:
    return _authenticate_as


@pytest.fixture
def resume_payload(
    default_location: dict[str, object],
) -> Callable[..., dict[str, object]]:
    def _payload(**overrides: object) -> dict[str, object]:
        return _resume_payload(default_location, **overrides)

    return _payload


@pytest.fixture
async def skill(session: AsyncSession) -> SkillModel:
    return await _create_skill(session, "Python")


@pytest.fixture
async def another_skill(session: AsyncSession) -> SkillModel:
    return await _create_skill(session, "FastAPI")
