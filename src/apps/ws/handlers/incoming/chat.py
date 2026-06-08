from typing import Any

from fastapi import WebSocket

from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.repositories.chat_message import ChatMessageRepository
from src.apps.chats.repositories.chat_participant import (
    ChatParticipantRepository,
)
from src.apps.chats.schemas.chat import CreateChatSchema
from src.apps.chats.schemas.chat_message import ChatMessageCreateRequest
from src.apps.shared.schemas.enums import OutgoingEvent
from src.apps.ws.handlers.outgoing.chat import (
    context,
    delete_objects,
    event,
    guard,
    leave_chat_channel,
    message_attachment_keys,
    parse,
    publish_to_users,
    publish_typing,
    remove_pending_tags,
)
from src.apps.ws.schemas.chat import (
    ChatRoomActionRequest,
    MessageActionRequest,
    ReadChatRequest,
    ScopedChatActionRequest,
    UpdateChatSettingsActionRequest,
    UpdateMessageActionRequest,
)
from src.core.websocket.broker import EventBroker
from src.core.websocket.channels import chat_channel, user_channel
from src.core.websocket.registry import connection_registry
from src.core.websocket.types import ConnectionId, UserId


async def handle_ping(
    _websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    _payload: dict[str, Any],
) -> None:
    await broker.send(connection_id, event(OutgoingEvent.pong))


async def handle_join_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(ChatRoomActionRequest, payload)
        session, user_uuid, _ = context(websocket)
        channel = chat_channel(data.chat_id)

        await ChatRepository.assert_participant(
            session, data.chat_id, user_uuid
        )
        connection_registry.join_channel(connection_id, channel)
        websocket.state.chat_ids.add(data.chat_id)

        await broker.send(
            connection_id,
            event(OutgoingEvent.chat_joined, chat_id=data.chat_id),
        )

    await guard(websocket, connection_id, broker, action)


async def handle_leave_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(ChatRoomActionRequest, payload)
        await leave_chat_channel(
            websocket=websocket,
            connection_id=connection_id,
            broker=broker,
            chat_id=data.chat_id,
            notify_self=True,
        )

    await guard(websocket, connection_id, broker, action)


async def handle_typing_start(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    await publish_typing(
        websocket, connection_id, broker, payload, OutgoingEvent.typing_start
    )


async def handle_typing_stop(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    await publish_typing(
        websocket, connection_id, broker, payload, OutgoingEvent.typing_stop
    )


async def handle_create_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(CreateChatSchema, payload)
        session, user_uuid, _ = context(websocket)

        chat = await ChatRepository.get_or_create_direct_chat(
            session, user_uuid, data.participant_id
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, chat.id
        )
        await session.commit()

        # TODO we might send ChatListItemResponse directly
        # so frontend does not need to refetch or invalidate cache
        evnt = event(
            OutgoingEvent.chat_created,
            chat_id=chat.id,
            participant_id=data.participant_id,
        )
        await publish_to_users(broker, participant_ids, evnt)

    await guard(websocket, connection_id, broker, action)


async def handle_send_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(ChatMessageCreateRequest, payload)
        session, user_uuid, _ = context(websocket)

        record = await ChatMessageRepository.create(
            session,
            user_uuid,
            message=data.message,
            chat_id=data.chat_id,
            reply_id=data.reply_id,
            participant_id=data.participant_id,
            attachments=data.attachments,
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, record.chat_id
        )
        new_keys = message_attachment_keys(record)
        message = ChatMessageRepository.to_response(record)
        await session.commit()

        await remove_pending_tags(new_keys)
        await publish_to_users(
            broker,
            participant_ids,
            event(OutgoingEvent.message_created, message=message),
        )

    await guard(websocket, connection_id, broker, action)


async def handle_update_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(UpdateMessageActionRequest, payload)
        session, user_uuid, _ = context(websocket)

        record, old_keys, new_keys = await ChatMessageRepository.update(
            session,
            user_uuid,
            data.message_id,
            chat_id=data.chat_id,
            message=data.message,
            attachments=data.attachments,
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, record.chat_id
        )
        message = ChatMessageRepository.to_response(record)
        await session.commit()

        await remove_pending_tags(new_keys)
        await delete_objects(old_keys)
        await publish_to_users(
            broker,
            participant_ids,
            event(OutgoingEvent.message_updated, message=message),
        )

    await guard(websocket, connection_id, broker, action)


async def handle_delete_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(MessageActionRequest, payload)
        session, user_uuid, _ = context(websocket)

        participant_ids = await ChatRepository.get_participant_ids(
            session, data.chat_id
        )
        object_keys = await ChatMessageRepository.attachment_keys(
            session, data.chat_id, data.message_id
        )
        await ChatMessageRepository.delete(
            session, user_uuid, data.chat_id, data.message_id
        )
        await session.commit()

        await delete_objects(object_keys)
        await publish_to_users(
            broker,
            participant_ids,
            event(
                OutgoingEvent.message_deleted,
                chat_id=data.chat_id,
                message_id=data.message_id,
            ),
        )

    await guard(websocket, connection_id, broker, action)


async def handle_read_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(ReadChatRequest, payload)
        session, user_uuid, _ = context(websocket)

        participant = await ChatParticipantRepository.set_last_seen_at(
            session, user_uuid, data.chat_id, data.last_seen_at
        )
        participant_ids = await ChatRepository.get_participant_ids(
            session, data.chat_id
        )
        await session.commit()

        await publish_to_users(
            broker,
            participant_ids,
            event(
                OutgoingEvent.chat_read,
                chat_id=data.chat_id,
                user_id=user_uuid,
                last_seen_at=participant.last_seen_at,
            ),
        )

    await guard(websocket, connection_id, broker, action)


async def handle_clear_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(ScopedChatActionRequest, payload)
        session, user_uuid, _ = context(websocket)

        if data.for_participant:
            participant_ids = await ChatRepository.get_participant_ids(
                session, data.chat_id
            )
            cleared_at = await ChatParticipantRepository.clear_for_everyone(
                session, data.chat_id, user_uuid
            )
            object_keys = await ChatMessageRepository.attachment_keys_until(
                session, data.chat_id, cleared_at
            )
            await ChatMessageRepository.delete_until(
                session, data.chat_id, cleared_at
            )
            await session.commit()

            await delete_objects(object_keys)
            await publish_to_users(
                broker,
                participant_ids,
                event(
                    OutgoingEvent.chat_cleared,
                    chat_id=data.chat_id,
                    user_id=user_uuid,
                    cleared_at=cleared_at,
                    for_participant=True,
                ),
            )
            return

        participant = await ChatParticipantRepository.clear_for_me(
            session, user_uuid, data.chat_id
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            event(
                OutgoingEvent.chat_cleared,
                chat_id=data.chat_id,
                user_id=user_uuid,
                cleared_at=participant.cleared_at,
                for_participant=False,
            ),
        )

    await guard(websocket, connection_id, broker, action)


async def handle_delete_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(ScopedChatActionRequest, payload)
        session, user_uuid, _ = context(websocket)

        if data.for_participant:
            participant_ids = await ChatRepository.get_participant_ids(
                session, data.chat_id
            )
            object_keys = await ChatRepository.attachment_keys(
                session, data.chat_id
            )
            await ChatRepository.delete_for_everyone(
                session, data.chat_id, user_uuid
            )
            await session.commit()

            await delete_objects(object_keys)
            await publish_to_users(
                broker,
                participant_ids,
                event(
                    OutgoingEvent.chat_deleted,
                    chat_id=data.chat_id,
                    user_id=user_uuid,
                    for_participant=True,
                ),
            )
            return

        participant = await ChatParticipantRepository.delete_for_me(
            session, data.chat_id, user_uuid
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            event(
                OutgoingEvent.chat_deleted,
                chat_id=data.chat_id,
                user_id=user_uuid,
                deleted_at=participant.deleted_at,
                for_participant=False,
            ),
        )

    await guard(websocket, connection_id, broker, action)


async def handle_update_chat_settings(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = parse(UpdateChatSettingsActionRequest, payload)
        session, user_uuid, _ = context(websocket)
        values = data.model_dump(
            include={"is_pinned", "is_muted", "is_archived"}, exclude_none=True
        )

        participant = await ChatParticipantRepository.update_settings(
            session, data.chat_id, user_uuid, values
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            event(
                OutgoingEvent.chat_settings_updated,
                chat_id=data.chat_id,
                is_pinned=participant.is_pinned,
                is_muted=participant.is_muted,
                is_archived=participant.is_archived,
            ),
        )

    await guard(websocket, connection_id, broker, action)
