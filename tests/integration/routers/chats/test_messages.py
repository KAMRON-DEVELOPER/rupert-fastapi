import pytest
from httpx import AsyncClient

from src.apps.chats.models import ChatMessageModel, ChatModel


@pytest.mark.integration
async def test_message_list_create_and_delete(
    auth_client_a: AsyncClient,
    chat_direct: ChatModel,
    message_in_direct: ChatMessageModel,
):
    list_res = await auth_client_a.get(
        f"/api/v1/chats/{chat_direct.id}/messages",
        params={"limit": 1},
    )
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["data"][0]["id"] == str(message_in_direct.id)

    create_res = await auth_client_a.post(
        f"/api/v1/chats/{chat_direct.id}/messages",
        json={"message": "hello"},
    )
    assert create_res.status_code == 201
    assert create_res.json()["message"] == "hello"

    delete_res = await auth_client_a.delete(
        f"/api/v1/chats/{chat_direct.id}/messages/{create_res.json()['id']}"
    )
    assert delete_res.status_code == 200


@pytest.mark.integration
async def test_cannot_delete_other_user_message(
    auth_client_b: AsyncClient,
    chat_direct: ChatModel,
    message_in_direct: ChatMessageModel,
):
    res = await auth_client_b.delete(
        f"/api/v1/chats/{chat_direct.id}/messages/{message_in_direct.id}"
    )

    assert res.status_code == 403
