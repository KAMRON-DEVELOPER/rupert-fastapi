from datetime import UTC, datetime
from uuid import UUID

from fastapi import WebSocket

from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.repositories.chat_participant import (
    ChatParticipantRepository,
)
from src.apps.shared.schemas.enums import OutgoingEvent
from src.apps.ws.handlers.outgoing.chat import (
    context,
    event,
    leave_chat_channel,
    publish_to_users,
)
from src.core.logger import logger
from src.core.websocket.broker import EventBroker
from src.core.websocket.registry import connection_registry
from src.core.websocket.types import ConnectionId


async def connect_handler(
    websocket: WebSocket, connection_id: ConnectionId, broker: EventBroker
) -> None:
    session, user_uuid, user_id = context(websocket)
    if connection_registry.user_has_connection(user_id, exclude=connection_id):
        return

    participant_ids = await ChatRepository.get_participant_ids(
        session, user_uuid
    )
    await publish_to_users(
        broker,
        participant_ids,
        event(OutgoingEvent.user_online, user_id=user_uuid),
    )


async def disconnect_handler(
    websocket: WebSocket, connection_id: ConnectionId, broker: EventBroker
) -> None:
    session, user_uuid, user_id = context(websocket)
    chat_ids: set[UUID] = websocket.state.chat_ids

    for chat_id in chat_ids:
        await leave_chat_channel(
            websocket=websocket,
            connection_id=connection_id,
            broker=broker,
            chat_id=chat_id,
            notify_self=False,
        )

    if connection_registry.user_has_connection(user_id, exclude=connection_id):
        logger.debug(f"[chat_ws] disconnected user={user_id}")
        return

    last_online_at = datetime.now(UTC)
    try:
        await ChatParticipantRepository.set_last_online_at(
            session, user_uuid, last_online_at
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, user_uuid
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception(f"[chat_ws] disconnect presence update failed: {e}")
        return

    await publish_to_users(
        broker,
        participant_ids,
        event(
            OutgoingEvent.user_offline,
            user_id=user_uuid,
            last_online_at=last_online_at,
        ),
    )
    logger.debug(f"[chat_ws] disconnected user={user_id}")
