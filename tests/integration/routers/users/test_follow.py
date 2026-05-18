from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.schemas.enums import FollowPolicy
from src.apps.users.models import UserModel
from src.apps.users.repositories.user import UsersRepository


@pytest.mark.integration
async def test_follow_auto_accept_duplicate_unfollow_and_lists(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
):
    follower = await make_user(email="follower@example.com")
    target = await make_user(
        email="target@example.com", first_name="Target", with_session=False
    )
    await authenticate_as(client, session, follower)

    follow_res = await client.post(f"/api/v1/users/{target.id}/follow")
    assert follow_res.status_code == 201
    assert follow_res.json()["status"] == "accepted"
    assert follow_res.json()["followingId"] == str(target.id)

    duplicate_res = await client.post(f"/api/v1/users/{target.id}/follow")
    assert duplicate_res.status_code == 409

    following_res = await client.get("/api/v1/users/following")
    assert following_res.status_code == 200
    assert following_res.json()["total"] == 1
    assert following_res.json()["data"][0]["followingId"] == str(target.id)

    await authenticate_as(client, session, target)
    followers_res = await client.get("/api/v1/users/followers")
    assert followers_res.status_code == 200
    assert followers_res.json()["total"] == 1
    assert followers_res.json()["data"][0]["followerId"] == str(follower.id)

    await authenticate_as(client, session, follower)
    unfollow_res = await client.delete(f"/api/v1/users/{target.id}/follow")
    assert unfollow_res.status_code == 200

    following_after_unfollow_res = await client.get("/api/v1/users/following")
    assert following_after_unfollow_res.status_code == 200
    assert following_after_unfollow_res.json()["total"] == 0


@pytest.mark.integration
async def test_follow_requires_approval_and_accepts_pending_request(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
):
    target = await make_user(email="approval-target@example.com")
    await UsersRepository.update(
        session, target.id, {"follow_policy": FollowPolicy.require_approval}
    )
    await session.flush()

    follower = await make_user(
        email="approval-follower@example.com",
        first_name="Follower",
        with_session=False,
    )
    await authenticate_as(client, session, follower)

    follow_res = await client.post(f"/api/v1/users/{target.id}/follow")
    assert follow_res.status_code == 201
    assert follow_res.json()["status"] == "pending"
    follow_id = follow_res.json()["id"]

    await authenticate_as(client, session, target)
    requests_res = await client.get("/api/v1/users/follow-requests")
    assert requests_res.status_code == 200
    assert requests_res.json()["total"] == 1
    assert requests_res.json()["data"][0]["id"] == follow_id

    patch_res = await client.patch(
        f"/api/v1/users/follow-requests/{follow_id}",
        json={"status": "accepted"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "accepted"


@pytest.mark.integration
async def test_follow_declines_pending_request(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
):
    target = await make_user(email="decline-target@example.com")
    await UsersRepository.update(
        session, target.id, {"follow_policy": FollowPolicy.require_approval}
    )
    await session.flush()

    follower = await make_user(
        email="decline-follower@example.com",
        first_name="Follower",
        with_session=False,
    )
    await authenticate_as(client, session, follower)
    follow_res = await client.post(f"/api/v1/users/{target.id}/follow")
    follow_id = follow_res.json()["id"]

    await authenticate_as(client, session, target)
    patch_res = await client.patch(
        f"/api/v1/users/follow-requests/{follow_id}",
        json={"status": "declined"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "declined"

    followers_res = await client.get("/api/v1/users/followers")
    assert followers_res.status_code == 200
    assert followers_res.json()["total"] == 0


@pytest.mark.integration
async def test_follow_rejects_self_follow_and_cross_user_request_updates(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
):
    target = await make_user(email="isolated-target@example.com")
    await UsersRepository.update(
        session, target.id, {"follow_policy": FollowPolicy.require_approval}
    )
    await session.flush()

    self_follow_res = await client.post(f"/api/v1/users/{target.id}/follow")
    assert self_follow_res.status_code == 400

    follower = await make_user(
        email="isolated-follower@example.com",
        first_name="Follower",
        with_session=False,
    )
    await authenticate_as(client, session, follower)
    follow_res = await client.post(f"/api/v1/users/{target.id}/follow")
    follow_id = follow_res.json()["id"]

    other = await make_user(
        email="isolated-other@example.com",
        first_name="Other",
        with_session=False,
    )
    await authenticate_as(client, session, other)
    patch_res = await client.patch(
        f"/api/v1/users/follow-requests/{follow_id}",
        json={"status": "accepted"},
    )
    assert patch_res.status_code == 404
