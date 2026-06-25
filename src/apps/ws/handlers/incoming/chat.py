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
    delete_objects,
    get_websocket_state,
    guard,
    leave_chat_channel,
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
from src.core.logger import logger
from src.core.websocket.broker import EventBroker
from src.core.websocket.channels import chat_channel, user_channel
from src.core.websocket.presence import presence
from src.core.websocket.registry import connection_registry
from src.core.websocket.types import ConnectionId, UserId


async def handle_ping(
    _websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    _payload: dict[str, Any],
) -> None:
    await broker.send(connection_id, {"type": OutgoingEvent.pong.value})


async def handle_join_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = ChatRoomActionRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)
        channel = chat_channel(data.chat_id)

        await ChatRepository.assert_participant(
            session, data.chat_id, user_uuid
        )
        connection_registry.join_channel(connection_id, channel)
        websocket.state.chat_ids.add(data.chat_id)

        await broker.send(
            connection_id,
            {
                "type": OutgoingEvent.chat_joined.value,
                "chatId": str(data.chat_id),
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_leave_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = ChatRoomActionRequest.model_validate(payload)
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
        logger.debug(f"[handle_create_chat] payload: {payload}")
        data = CreateChatSchema.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)

        chat = await ChatRepository.get_or_create_direct_chat(
            session, user_uuid, data.participant_id
        )
        # Why we need to fetch because we already have all
        participant_id = await ChatRepository.get_user_participant_id(
            session, user_id=user_uuid
        )
        await session.commit()

        logger.debug(f"chat: {chat}")
        logger.debug(f"participant_id: {participant_id}")

        item = await ChatRepository.get_list_item(session, chat.id, user_uuid)
        item.user.is_online = await presence.is_online(
            UserId(str(data.participant_id))
        )

        logger.debug(f"item: {item}")

        await publish_to_users(
            broker,
            [user_uuid, participant_id],
            {
                "type": OutgoingEvent.chat_created.value,
                "item": item.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_unset=True,
                    exclude_none=True,
                ),
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_send_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = ChatMessageCreateRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)

        chat_msg = await ChatMessageRepository.create(
            session,
            sender_id=user_uuid,
            message=data.message,
            chat_id=data.chat_id,
            reply_id=data.reply_id,
            attachments=data.attachments,
        )

        participant_id = await ChatRepository.get_user_participant_id(
            session, user_id=user_uuid
        )

        new_keys = [
            link.attachment.object_key for link in chat_msg.attachment_links
        ]

        message = ChatMessageRepository.to_response(chat_msg)

        await session.commit()

        await remove_pending_tags(new_keys)

        await publish_to_users(
            broker,
            [user_uuid, participant_id],
            {
                "type": OutgoingEvent.message_created.value,
                "message": message.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_unset=True,
                    exclude_none=True,
                ),
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_update_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = UpdateMessageActionRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)

        record, old_keys, new_keys = await ChatMessageRepository.update(
            session,
            user_uuid,
            data.message_id,
            chat_id=data.chat_id,
            message=data.message,
            attachments=data.attachments,
        )
        participant_id = await ChatRepository.get_user_participant_id(
            session, user_id=user_uuid
        )
        message = ChatMessageRepository.to_response(record)
        await session.commit()

        await remove_pending_tags(new_keys)
        await delete_objects(old_keys)
        await publish_to_users(
            broker,
            [user_uuid, participant_id],
            {
                "type": OutgoingEvent.message_updated.value,
                "message": message.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_unset=True,
                    exclude_none=True,
                ),
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_delete_message(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = MessageActionRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)

        participant_id = await ChatRepository.get_user_participant_id(
            session, user_id=user_uuid
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
            [user_uuid, participant_id],
            {
                "value": OutgoingEvent.message_deleted.value,
                "chatId": str(data.chat_id),
                "messageId": str(data.message_id),
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_read_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = ReadChatRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)

        participant = await ChatParticipantRepository.set_last_seen_at(
            session, user_uuid, data.chat_id, data.last_seen_at
        )
        participant_id = await ChatRepository.get_user_participant_id(
            session, user_id=user_uuid
        )
        await session.commit()

        await publish_to_users(
            broker,
            [user_uuid, participant_id],
            {
                "type": OutgoingEvent.chat_read.value,
                "chatId": str(data.chat_id),
                "userId": str(user_uuid),
                "lastSeenAt": (
                    participant.last_seen_at.isoformat()
                    if participant.last_seen_at is not None
                    else None
                ),
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_clear_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = ScopedChatActionRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)

        if data.for_participant:
            participant_id = await ChatRepository.get_user_participant_id(
                session, user_id=user_uuid
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
                [user_uuid, participant_id],
                {
                    "type": OutgoingEvent.chat_cleared.value,
                    "chatId": str(data.chat_id),
                    "userId": str(user_uuid),
                    "clearedAt": cleared_at.isoformat(),
                    "forParticipant": True,
                },
            )
            return

        participant = await ChatParticipantRepository.clear_for_me(
            session, user_uuid, data.chat_id
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            {
                "type": OutgoingEvent.chat_cleared.value,
                "chatId": str(data.chat_id),
                "userId": str(user_uuid),
                "clearedAt": (
                    participant.cleared_at.isoformat()
                    if participant.cleared_at is not None
                    else None
                ),
                "forParticipant": False,
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_delete_chat(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = ScopedChatActionRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)

        if data.for_participant:
            participant_id = await ChatRepository.get_user_participant_id(
                session, user_id=user_uuid
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
                [user_uuid, participant_id],
                {
                    "type": OutgoingEvent.chat_deleted.value,
                    "chatId": str(data.chat_id),
                    "userId": str(user_uuid),
                    "forParticipant": True,
                },
            )
            return

        participant = await ChatParticipantRepository.delete_for_me(
            session, data.chat_id, user_uuid
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            {
                "type": OutgoingEvent.chat_deleted.value,
                "chatId": str(data.chat_id),
                "userId": str(user_uuid),
                "deletedAt": (
                    participant.deleted_at.isoformat()
                    if participant.deleted_at is not None
                    else None
                ),
                "forParticipant": False,
            },
        )

    await guard(websocket, connection_id, broker, action)


async def handle_update_chat_settings(
    websocket: WebSocket,
    connection_id: ConnectionId,
    broker: EventBroker,
    payload: dict[str, Any],
) -> None:
    async def action() -> None:
        data = UpdateChatSettingsActionRequest.model_validate(payload)
        session, user_uuid, _, _ = get_websocket_state(websocket)
        values = data.model_dump(
            include={"is_pinned", "is_muted", "is_archived"},
            by_alias=True,
            exclude_unset=True,
            exclude_none=True,
        )

        participant = await ChatParticipantRepository.update_settings(
            session, data.chat_id, user_uuid, values
        )
        await session.commit()

        await broker.publish(
            user_channel(UserId(str(user_uuid))),
            {
                "type": OutgoingEvent.chat_settings_updated.value,
                "chatId": str(data.chat_id),
                "isPinned": participant.is_pinned,
                "isMuted": participant.is_muted,
                "isArchived": participant.is_archived,
            },
        )

    await guard(websocket, connection_id, broker, action)
