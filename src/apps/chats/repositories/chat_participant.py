from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, literal, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.chats.models import ChatParticipantModel
from src.core.logger import logger


class ChatParticipantRepository:
    @classmethod
    async def create(cls, session: AsyncSession, user_id: UUID, chat_id: UUID):
        record = ChatParticipantModel(
            user_id=user_id, chat_id=chat_id, last_online_at=datetime.now(UTC)
        )

        try:
            session.add(record)
            await session.flush()
            return record
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] add integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chat participant already exists",
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] add: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating chat participant",
            )

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID, chat_id: UUID):
        stmt = (
            delete(ChatParticipantModel)
            .where(
                ChatParticipantModel.user_id == user_id,
                ChatParticipantModel.chat_id == chat_id,
            )
            .returning(ChatParticipantModel.id)
        )

        try:
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat participant not found",
                )
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] remove: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while removing chat participant",
            )

    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, user_id: UUID, chat_id: UUID
    ):
        stmt = (
            select(ChatParticipantModel)
            .options(selectinload(ChatParticipantModel.user))
            .where(
                ChatParticipantModel.user_id == user_id,
                ChatParticipantModel.chat_id == chat_id,
            )
        )

        try:
            participant = await session.scalar(stmt)
        except SQLAlchemyError as e:
            logger.error(f"[ChatParticipantRepository] get: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving chat participant",
            )

        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant",
            )

        return participant

    @classmethod
    async def list_by_chat(
        cls, session: AsyncSession, chat_id: UUID
    ) -> Sequence[ChatParticipantModel]:
        stmt = (
            select(ChatParticipantModel)
            .options(selectinload(ChatParticipantModel.user))
            .where(ChatParticipantModel.chat_id == chat_id)
            .order_by(ChatParticipantModel.created_at.asc())
        )

        try:
            return (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            logger.error(f"[ChatParticipantRepository] list_by_chat: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving chat participants",
            )

    @classmethod
    async def set_last_seen_at(
        cls,
        session: AsyncSession,
        user_id: UUID,
        chat_id: UUID,
        last_seen_at: datetime,
    ) -> ChatParticipantModel:
        epoch = datetime(1970, 1, 1, tzinfo=UTC)

        stmt = (
            update(ChatParticipantModel)
            .where(ChatParticipantModel.chat_id == chat_id)
            .where(ChatParticipantModel.user_id == user_id)
            .where(ChatParticipantModel.deleted_at.is_(None))
            .values(
                last_seen_at=func.greatest(
                    func.coalesce(
                        ChatParticipantModel.last_seen_at, literal(epoch)
                    ),
                    last_seen_at,
                )
            )
            .returning(ChatParticipantModel)
        )

        try:
            participant = await session.scalar(stmt)
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] set_last_seen_at: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not update 'last read at' state",
            )

        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )
        return participant

    @classmethod
    async def set_last_online_at(
        cls, session: AsyncSession, user_id: UUID, last_online_at: datetime
    ) -> None:
        try:
            await session.execute(
                update(ChatParticipantModel)
                .where(ChatParticipantModel.user_id == user_id)
                .values(last_online_at=last_online_at)
            )
            await session.flush()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] set_last_online_at: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not update online state",
            )

    @classmethod
    async def clear_for_me(
        cls, session: AsyncSession, user_id: UUID, chat_id: UUID
    ):
        participant = await cls.get_by_id(session, user_id, chat_id)

        participant.cleared_at = datetime.now(UTC)
        participant.deleted_at = None

        try:
            await session.flush()
            return participant
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] clear_for_me: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while clearing chat participant",
            )

    @classmethod
    async def clear_for_everyone(
        cls, session: AsyncSession, chat_id: UUID, user_id: UUID
    ) -> datetime:
        await cls.get_by_id(session, user_id, chat_id)
        now = datetime.now(UTC)
        try:
            await session.execute(
                update(ChatParticipantModel)
                .where(ChatParticipantModel.chat_id == chat_id)
                .values(cleared_at=now, deleted_at=None, last_seen_at=now)
            )
            await session.flush()
            return now
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] clear_for_everyone: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while clearing chat history",
            )

    @classmethod
    async def delete_for_me(
        cls, session: AsyncSession, chat_id: UUID, user_id: UUID
    ):
        participant = await cls.get_by_id(session, user_id, chat_id)

        now = datetime.now(UTC)
        participant.deleted_at = now
        participant.cleared_at = now

        try:
            await session.flush()
            return participant
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] delete_for_me: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting chat participant",
            )

    @classmethod
    async def update_settings(
        cls,
        session: AsyncSession,
        chat_id: UUID,
        user_id: UUID,
        values: dict[str, object],
    ) -> ChatParticipantModel:
        participant = await cls.get_by_id(session, user_id, chat_id)
        for field, value in values.items():
            if value is not None:
                setattr(participant, field, value)
        try:
            await session.flush()
            return participant
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatParticipantRepository] update_settings: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating chat settings",
            )
