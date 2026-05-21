from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from httpx_ws import WebSocketDisconnect, WebSocketUpgradeError, aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from src.apps.chats.models import ChatMessageModel, ChatModel
from src.apps.chats.routes.chats import _chat_room
from src.apps.shared.schemas.enums import ChatEvent
from src.apps.users.models import UserModel
from src.core.websocket_manager import websocket_manager


@pytest.mark.integration
async def test_ws_invalid_token():
    transport = ASGIWebSocketTransport(app)
    async with AsyncClient(transport=transport) as client:
        client.cookies.set("access_token", "bad")
        with pytest.raises(WebSocketUpgradeError) as exc:
            async with aconnect_ws(
                "http://server/api/v1/chats/00000000-0000-0000-0000-000000000000/ws",
                client,
            ):
                pass

    assert exc.value.response.status_code == 401


@pytest.mark.integration
async def test_ws_non_member(
    client: AsyncClient,
    session: AsyncSession,
    make_user: Callable[..., Awaitable[UserModel]],
    authenticate_as: Callable[
        [AsyncClient, AsyncSession, UserModel], Awaitable[str]
    ],
    chat_direct: ChatModel,
):
    user = await make_user(email="ws-other@example.com", with_session=False)
    token = await authenticate_as(client, session, user)
    transport = ASGIWebSocketTransport(app)

    async with AsyncClient(transport=transport) as ws_client:
        ws_client.cookies.set("access_token", token)
        with pytest.raises(WebSocketDisconnect) as exc:
            async with aconnect_ws(
                f"http://server/api/v1/chats/{chat_direct.id}/ws",
                ws_client,
            ):
                pass

    assert exc.value.code == 4003


@pytest.mark.integration
async def test_ws_message_broadcast(
    client: AsyncClient,
    chat_direct: ChatModel,
    auth_token_a: str,
    auth_token_b: str,
):
    assert client is not None
    transport = ASGIWebSocketTransport(app)
    async with AsyncClient(transport=transport) as sender:
        sender.cookies.set("access_token", auth_token_a)
        async with AsyncClient(transport=transport) as receiver:
            receiver.cookies.set("access_token", auth_token_b)
            async with aconnect_ws(
                f"http://server/api/v1/chats/{chat_direct.id}/ws",
                sender,
            ) as ws_a:
                async with aconnect_ws(
                    f"http://server/api/v1/chats/{chat_direct.id}/ws",
                    receiver,
                ) as ws_b:
                    await ws_a.send_json(
                        {
                            "type": ChatEvent.sent_message.value,
                            "message": "hello",
                        }
                    )
                    res = await ws_b.receive_json()

    assert res["message"] == "hello"


@pytest.mark.integration
async def test_ws_typing_indicator(
    client: AsyncClient,
    session: AsyncSession,
    chat_direct: ChatModel,
    auth_token_a: str,
    auth_token_b: str,
    user_a: UserModel,
):
    assert client is not None
    transport = ASGIWebSocketTransport(app)
    async with AsyncClient(transport=transport) as sender:
        sender.cookies.set("access_token", auth_token_a)
        async with AsyncClient(transport=transport) as receiver:
            receiver.cookies.set("access_token", auth_token_b)
            async with aconnect_ws(
                f"http://server/api/v1/chats/{chat_direct.id}/ws",
                sender,
            ) as ws_a:
                async with aconnect_ws(
                    f"http://server/api/v1/chats/{chat_direct.id}/ws",
                    receiver,
                ) as ws_b:
                    await ws_a.send_json({"type": ChatEvent.typing_start.value})
                    res = await ws_b.receive_json()

    assert res == {"type": "typing_start", "user_id": str(user_a.id)}

    message = await session.scalar(
        select(ChatMessageModel).where(
            ChatMessageModel.chat_id == chat_direct.id
        )
    )
    assert message is None


@pytest.mark.integration
async def test_ws_ping_pong(
    client: AsyncClient,
    chat_direct: ChatModel,
    auth_token_a: str,
):
    assert client is not None
    transport = ASGIWebSocketTransport(app)
    async with AsyncClient(transport=transport) as client:
        client.cookies.set("access_token", auth_token_a)
        async with aconnect_ws(
            f"http://server/api/v1/chats/{chat_direct.id}/ws",
            client,
        ) as ws:
            await ws.send_json({"type": ChatEvent.ping.value})
            res = await ws.receive_json()

    assert res == {"type": "pong"}


@pytest.mark.integration
async def test_ws_unknown_type(
    client: AsyncClient,
    chat_direct: ChatModel,
    auth_token_a: str,
):
    assert client is not None
    transport = ASGIWebSocketTransport(app)
    async with AsyncClient(transport=transport) as client:
        client.cookies.set("access_token", auth_token_a)
        async with aconnect_ws(
            f"http://server/api/v1/chats/{chat_direct.id}/ws",
            client,
        ) as ws:
            await ws.send_json({"type": "unknown"})
            res = await ws.receive_json()

    assert res == {"type": "error", "detail": "unknown message type"}


@pytest.mark.integration
async def test_ws_disconnect_cleanup(
    client: AsyncClient,
    chat_direct: ChatModel,
    auth_token_a: str,
):
    assert client is not None
    room = _chat_room(chat_direct.id)
    transport = ASGIWebSocketTransport(app)
    async with AsyncClient(transport=transport) as client:
        client.cookies.set("access_token", auth_token_a)
        async with aconnect_ws(
            f"http://server/api/v1/chats/{chat_direct.id}/ws",
            client,
        ):
            assert websocket_manager.room_size(room) == 1

    assert websocket_manager.room_size(room) == 0
