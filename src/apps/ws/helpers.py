from uuid import UUID

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.websocket.types import UserId


def get_websocket_state(
    ws: WebSocket,
) -> tuple[AsyncSession, UUID, UserId, set]:
    return (
        ws.state.session,
        ws.state.user_uuid,
        ws.state.user_id,
        ws.state.chat_ids,
    )


def set_websocket_state(
    ws: WebSocket,
    session: AsyncSession,
    user_uuid: UUID,
    user_id: UserId,
    chat_ids: set | None = None,
):
    ws.state.session = session
    ws.state.user_uuid = user_uuid
    ws.state.user_id = user_id
    ws.state.chat_ids = chat_ids or set()
