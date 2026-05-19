from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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


def _company_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Rupert Labs",
        "tagline": "Hiring better",
        "description": "A product company for developer hiring.",
        "websiteUrl": "https://rupert.example.com",
        "type": "startup",
        "contactEmail": "hello@rupert.example.com",
        "contactPhone": "+998901234567",
        "country": "UZ",
        "city": "Tashkent",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def authenticate_as() -> Callable[
    [AsyncClient, AsyncSession, UserModel], Awaitable[str]
]:
    return _authenticate_as


@pytest.fixture
def company_payload() -> Callable[..., dict[str, object]]:
    return _company_payload


@pytest.fixture
def create_company(
    client: AsyncClient, company_payload: Callable[..., dict[str, object]]
) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _create_company(**overrides: object) -> dict[str, Any]:
        res = await client.post(
            "/api/v1/companies/", json=company_payload(**overrides)
        )
        assert res.status_code == 201
        return res.json()

    return _create_company
