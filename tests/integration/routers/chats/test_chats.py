from collections.abc import Awaitable, Callable
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.chats.models import ChatModel, ChatParticipantModel
from src.apps.users.models import UserModel


@pytest.mark.integration
async def test_chat_create_list_detail_clear_and_delete(
    auth_client_a: AsyncClient,
    chat_direct: ChatModel,
    message_in_direct,
    session: AsyncSession,
    user_b: UserModel,
):
    assert message_in_direct.chat_id == chat_direct.id

    list_res = await auth_client_a.get("/api/v1/chats/", params={"limit": 1})
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["data"][0]["id"] == str(chat_direct.id)
    assert list_res.json()["data"][0]["participant"]["id"] == str(user_b.id)
    assert list_res.json()["data"][0]["lastMessage"]["message"] == (
        "Seeded message"
    )

    detail_res = await auth_client_a.get(f"/api/v1/chats/{chat_direct.id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["lastMessage"]["message"] == "Seeded message"

    clear_res = await auth_client_a.delete(
        f"/api/v1/chats/{chat_direct.id}/clear"
    )
    assert clear_res.status_code == 200

    cleared_messages_res = await auth_client_a.get(
        f"/api/v1/chats/{chat_direct.id}/messages"
    )
    assert cleared_messages_res.status_code == 200
    assert cleared_messages_res.json()["total"] == 0

    delete_res = await auth_client_a.delete(f"/api/v1/chats/{chat_direct.id}")
    assert delete_res.status_code == 200

    participant = await session.scalar(
        select(ChatParticipantModel).where(
            ChatParticipantModel.chat_id == chat_direct.id,
            ChatParticipantModel.user_id != user_b.id,
        )
    )
    assert participant is not None
    assert participant.deleted_at is not None
    assert participant.cleared_at is not None


@pytest.mark.integration
async def test_create_duplicate_and_missing_paths(
    auth_client_a: AsyncClient,
    user_b: UserModel,
):
    res = await auth_client_a.post(
        "/api/v1/chats/", json={"participantId": str(user_b.id)}
    )
    assert res.status_code == 201

    duplicate_res = await auth_client_a.post(
        "/api/v1/chats/", json={"participantId": str(user_b.id)}
    )
    assert duplicate_res.status_code == 409

    missing_res = await auth_client_a.get(f"/api/v1/chats/{uuid4()}")
    assert missing_res.status_code == 404


@pytest.mark.integration
async def test_non_member_cannot_read_chat(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    chat_direct: ChatModel,
):
    user = await make_user(email="chat-other@example.com", with_session=False)
    await authenticate_as(client, session, user)

    res = await client.get(f"/api/v1/chats/{chat_direct.id}")
    assert res.status_code == 403


@pytest.mark.integration
async def test_clear_and_delete_for_other(
    auth_client_a: AsyncClient,
    chat_direct: ChatModel,
    message_in_direct,
    session: AsyncSession,
):
    assert message_in_direct.chat_id == chat_direct.id

    clear_res = await auth_client_a.delete(
        f"/api/v1/chats/{chat_direct.id}/clear",
        params={"also_for_other": True},
    )
    assert clear_res.status_code == 200

    messages_res = await auth_client_a.get(
        f"/api/v1/chats/{chat_direct.id}/messages"
    )
    assert messages_res.status_code == 200
    assert messages_res.json()["total"] == 0

    chat = await session.scalar(
        select(ChatModel).where(ChatModel.id == chat_direct.id)
    )
    assert chat is not None

    delete_res = await auth_client_a.delete(
        f"/api/v1/chats/{chat_direct.id}",
        params={"also_for_other": True},
    )
    assert delete_res.status_code == 200

    deleted = await session.scalar(
        select(ChatModel).where(ChatModel.id == chat_direct.id)
    )
    assert deleted is None
