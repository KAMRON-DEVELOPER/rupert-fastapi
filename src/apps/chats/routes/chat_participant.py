from typing import Annotated
from uuid import UUID

from fastapi import Query, status

from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.repositories.chat_message import ChatMessageRepository
from src.apps.chats.repositories.chat_participant import (
    ChatParticipantRepository,
)
from src.apps.chats.schemas.chat_participant import (
    ChatSettingsRequest,
    LastSeenAtRequest,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import chats_router


@chats_router.patch("/{chat_id}/settings", status_code=204)
async def update_chat_settings(
    session: sessionDep,
    auth: authDep,
    chat_id: UUID,
    schm: ChatSettingsRequest,
):
    user_id, _, _ = auth
    await ChatParticipantRepository.update_settings(
        session, chat_id, user_id, schm.model_dump(exclude_unset=True)
    )
    await session.commit()


@chats_router.post("/{chat_id}/last-seen-at")
async def set_last_seen_at(
    session: sessionDep,
    auth: authDep,
    chat_id: UUID,
    schm: LastSeenAtRequest,
):
    user_id, _, _ = auth
    await ChatParticipantRepository.set_last_seen_at(
        session, chat_id, user_id, schm.last_seen_at
    )
    await session.commit()


@chats_router.post("/{chat_id}/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    session: sessionDep,
    auth: authDep,
    chat_id: UUID,
    including_other: Annotated[bool, Query()] = False,
):
    user_id, _, _ = auth

    if including_other:
        until = await ChatParticipantRepository.clear_for_everyone(
            session, chat_id, user_id
        )
        await ChatMessageRepository.delete_until(session, chat_id, until)
    else:
        await ChatParticipantRepository.clear_for_me(session, chat_id, user_id)

    await session.commit()


@chats_router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    session: sessionDep,
    auth: authDep,
    chat_id: UUID,
    including_other: Annotated[bool, Query()] = False,
):
    user_id, _, _ = auth

    if including_other:
        await ChatRepository.assert_participant(session, chat_id, user_id)
        await ChatRepository.delete(session, chat_id)
    else:
        await ChatParticipantRepository.delete_for_me(session, chat_id, user_id)

    await session.commit()
