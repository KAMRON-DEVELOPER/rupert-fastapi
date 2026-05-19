from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import SessionModel, UserModel
from src.apps.users.repositories.session import SessionsRepository


@pytest.mark.integration
async def test_session_listing_and_single_revocation(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    user = await make_user()
    other_session = await SessionsRepository.create(
        session,
        "other-refresh-token",
        user.id,
        user_agent="pytest-2",
        ip_addr="127.0.0.2",
        device_name="other",
    )
    await session.flush()

    list_res = await client.get("/api/v1/users/sessions")
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert len(sessions) == 2
    assert all("refreshToken" not in item for item in sessions)
    assert {item["deviceName"] for item in sessions} == {"test", "other"}

    revoke_res = await client.delete(
        f"/api/v1/users/sessions/{other_session.id}"
    )
    assert revoke_res.status_code == 200

    remaining_sessions = (
        await session.scalars(
            select(SessionModel).where(SessionModel.user_id == user.id)
        )
    ).all()
    assert len(remaining_sessions) == 1
    assert remaining_sessions[0].device_name == "test"


@pytest.mark.integration
async def test_session_revoking_current_session_clears_auth_cookies(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    user = await make_user()
    current_session = await session.scalar(
        select(SessionModel).where(SessionModel.user_id == user.id)
    )
    assert current_session is not None

    revoke_res = await client.delete(
        f"/api/v1/users/sessions/{current_session.id}"
    )
    set_cookie_headers = revoke_res.headers.get_list("set-cookie")

    assert revoke_res.status_code == 200
    assert "access_token" not in client.cookies
    assert "refresh_token" not in client.cookies
    assert any(h.startswith("access_token=") for h in set_cookie_headers)
    assert any(h.startswith("refresh_token=") for h in set_cookie_headers)


@pytest.mark.integration
async def test_session_revocation_invalidates_existing_access_token(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    user = await make_user()
    current_session = await session.scalar(
        select(SessionModel).where(SessionModel.user_id == user.id)
    )
    assert current_session is not None

    await SessionsRepository.delete_by_id(session, user.id, current_session.id)
    await session.flush()

    probe_res = await client.get("/api/v1/users/auth/probe")

    assert probe_res.status_code == 200
    assert probe_res.json() == {"isAuthenticated": False}
    assert "access_token" not in client.cookies
    assert "refresh_token" not in client.cookies


@pytest.mark.integration
async def test_session_rejects_revoking_another_users_session(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    await make_user(email="session-owner@example.com")
    other = await make_user(
        email="session-other@example.com",
        first_name="Other",
        with_session=False,
    )
    other_session = await SessionsRepository.create(
        session,
        "other-user-refresh-token",
        other.id,
        user_agent="pytest-other",
        ip_addr="127.0.0.3",
        device_name="other-user",
    )
    await session.flush()

    revoke_res = await client.delete(
        f"/api/v1/users/sessions/{other_session.id}"
    )
    assert revoke_res.status_code == 404


@pytest.mark.integration
async def test_session_revoke_all_preserves_current_session_by_default(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    user = await make_user()
    await SessionsRepository.create(
        session,
        "other-refresh-token",
        user.id,
        user_agent="pytest-2",
        ip_addr="127.0.0.2",
        device_name="other",
    )
    await session.flush()

    revoke_res = await client.delete("/api/v1/users/sessions")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["message"] == "Revoked 1 sessions"

    remaining_sessions = (
        await session.scalars(
            select(SessionModel).where(SessionModel.user_id == user.id)
        )
    ).all()
    assert len(remaining_sessions) == 1
    assert remaining_sessions[0].device_name == "test"


@pytest.mark.integration
async def test_session_revoke_all_can_include_current_session(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
):
    user = await make_user()
    await SessionsRepository.create(
        session,
        "other-refresh-token",
        user.id,
        user_agent="pytest-2",
        ip_addr="127.0.0.2",
        device_name="other",
    )
    await session.flush()

    revoke_res = await client.delete(
        "/api/v1/users/sessions", params={"include_current": True}
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["message"] == "Revoked 2 sessions"

    remaining_sessions = (
        await session.scalars(
            select(SessionModel).where(SessionModel.user_id == user.id)
        )
    ).all()
    assert remaining_sessions == []
