from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.chats.models import ChatMessageModel, ChatModel
from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.repositories.chat_message import ChatMessageRepository
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

    return access_token


@pytest.fixture
def authenticate_as() -> Callable[
    [AsyncClient, AsyncSession, UserModel], Awaitable[str]
]:
    return _authenticate_as


@pytest.fixture
async def user_a(
    make_user: Callable[..., Awaitable[UserModel]],
) -> UserModel:
    return await make_user(email="chat-a@example.com", with_session=False)


@pytest.fixture
async def user_b(
    make_user: Callable[..., Awaitable[UserModel]],
) -> UserModel:
    return await make_user(email="chat-b@example.com", with_session=False)


@pytest.fixture
async def auth_token_a(
    client: AsyncClient,
    session: AsyncSession,
    user_a: UserModel,
) -> str:
    return await _authenticate_as(client, session, user_a)


@pytest.fixture
async def auth_token_b(
    client: AsyncClient,
    session: AsyncSession,
    user_b: UserModel,
) -> str:
    return await _authenticate_as(client, session, user_b)


@pytest.fixture
async def auth_client_a(
    client: AsyncClient,
    session: AsyncSession,
    user_a: UserModel,
) -> AsyncClient:
    await _authenticate_as(client, session, user_a)
    return client


@pytest.fixture
async def auth_client_b(
    client: AsyncClient,
    session: AsyncSession,
    user_b: UserModel,
) -> AsyncClient:
    await _authenticate_as(client, session, user_b)
    return client


@pytest.fixture
async def chat_direct(
    session: AsyncSession,
    user_a: UserModel,
    user_b: UserModel,
) -> ChatModel:
    chat = await ChatRepository.create(session, user_a.id, user_b.id)
    await session.flush()
    return chat


@pytest.fixture
async def message_in_direct(
    session: AsyncSession,
    chat_direct: ChatModel,
    user_a: UserModel,
) -> ChatMessageModel:
    message = await ChatMessageRepository.create(
        session,
        chat_direct.id,
        user_a.id,
        "Seeded message",
    )
    await session.flush()
    return message
