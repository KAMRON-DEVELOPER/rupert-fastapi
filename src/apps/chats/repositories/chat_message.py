from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.chats.models import ChatMessageModel, ChatParticipantModel
from src.apps.chats.repositories.chat import ChatRepository
from src.apps.shared.schemas import PaginatedResponse
from src.core.logger import logger


class ChatMessageRepository:
    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        sender_id: UUID,
        *,
        message: str | None = None,
        image_urls: list[str] | None = None,
        video_urls: list[str] | None = None,
        chat_id: UUID | None = None,
        reply_id: UUID | None = None,
        participant_id: UUID | None = None,
    ) -> ChatMessageModel:
        if chat_id is None:
            if participant_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="participant_id is required when chat_id is not provided",
                )

            chat = await ChatRepository.get_or_create_direct_chat(
                session, sender_id, participant_id
            )
            chat_id = chat.id
        else:
            await ChatRepository.assert_participant(session, chat_id, sender_id)

        if reply_id is not None:
            reply_chat_id = await session.scalar(
                select(ChatMessageModel.chat_id).where(
                    ChatMessageModel.id == reply_id
                )
            )
            if reply_chat_id != chat_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="reply_id must reference a message from the same chat",
                )

        record = ChatMessageModel(
            sender_id=sender_id,
            message=message,
            image_urls=image_urls,
            video_urls=video_urls,
            chat_id=chat_id,
            reply_id=reply_id,
        )

        try:
            session.add(record)
            await session.flush()

            await session.execute(
                update(ChatParticipantModel)
                .where(ChatParticipantModel.chat_id == chat_id)
                .where(ChatParticipantModel.user_id == sender_id)
                .values(last_seen_at=record.created_at, deleted_at=None)
            )
            await session.flush()

            return record
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ChatMessageRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chat message references invalid data",
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatMessageRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating chat message",
            )

    @classmethod
    async def delete(
        cls,
        session: AsyncSession,
        user_id: UUID,
        chat_id: UUID,
        message_id: UUID,
    ) -> None:
        message = await cls.get_by_id(session, message_id)
        await ChatRepository.assert_participant(
            session, message.chat_id, user_id
        )

        if message.sender_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can delete only your own messages",
            )

        try:
            await session.execute(
                delete(ChatMessageModel).where(
                    ChatMessageModel.chat_id == chat_id,
                    ChatMessageModel.id == message_id,
                )
            )
            await session.flush()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatMessageRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting chat message",
            )

    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        message_id: UUID,
    ) -> ChatMessageModel:
        stmt = select(ChatMessageModel).where(ChatMessageModel.id == message_id)

        try:
            record = await session.scalar(stmt)
        except SQLAlchemyError as e:
            logger.error(f"[ChatMessageRepository] get_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving chat message",
            )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat message not found",
            )

        return record

    @classmethod
    async def get_many(
        cls,
        session: AsyncSession,
        chat_id: UUID,
        user_id: UUID,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[ChatMessageModel]:
        try:
            participant = await session.scalar(
                select(ChatParticipantModel).where(
                    ChatParticipantModel.chat_id == chat_id,
                    ChatParticipantModel.user_id == user_id,
                    ChatParticipantModel.deleted_at.is_(None),
                )
            )

            if not participant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat not found",
                )

            filters = [ChatMessageModel.chat_id == chat_id]
            if participant.cleared_at:
                filters.append(
                    ChatMessageModel.created_at > participant.cleared_at
                )

            total = (
                await session.scalar(
                    select(func.count(ChatMessageModel.id)).where(*filters)
                )
                or 0
            )

            records = (
                await session.scalars(
                    select(ChatMessageModel)
                    .where(*filters)
                    .order_by(ChatMessageModel.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()

            return PaginatedResponse(data=list(records), total=total)
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"[ChatMessageRepository] get_chat_messages: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving chat messages",
            )

    @classmethod
    async def delete_until(
        cls, session: AsyncSession, chat_id: UUID, until: datetime
    ) -> None:
        stmt = (
            delete(ChatMessageModel)
            .where(
                ChatMessageModel.chat_id == chat_id,
                ChatMessageModel.created_at <= until,
            )
            .returning(ChatMessageModel.id)
        )

        try:
            await session.execute(stmt)
            await session.flush()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatMessageRepository] delete_until: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting chat messages",
            )
