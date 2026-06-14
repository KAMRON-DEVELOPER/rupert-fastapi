from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.chats.models import (
    ChatMessageAttachmentLink,
    ChatMessageModel,
    ChatParticipantModel,
)
from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.schemas.chat_message import (
    ChatListLastMessageResponse,
    ChatMessageResponse,
)
from src.apps.shared.models.attachment import AttachmentModel
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.apps.shared.schemas.attachment import (
    AttachmentIdWithPositionRequest,
    AttachmentWithPositionResponse,
)
from src.apps.shared.schemas.enums import AttachmentStatus
from src.core.logger import logger


class ChatMessageRepository:
    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        *,
        sender_id: UUID,
        message: str | None = None,
        chat_id: UUID,
        reply_id: UUID | None = None,
        attachments: list[AttachmentIdWithPositionRequest],
    ) -> ChatMessageModel:
        await ChatRepository.assert_participant(session, chat_id, sender_id)

        if reply_id:
            await cls._assert_reply_belongs_to_chat(session, chat_id, reply_id)

        attachment_records = await cls._pending_attachments(
            session, sender_id, attachments
        )

        record = ChatMessageModel(
            sender_id=sender_id,
            message=_clean_message(message),
            chat_id=chat_id,
            reply_id=reply_id,
        )

        try:
            session.add(record)
            await session.flush()

            for item in attachments:
                attachment = attachment_records[item.attachment_id]
                attachment.status = AttachmentStatus.ready
                record.attachment_links.append(
                    ChatMessageAttachmentLink(
                        attachment_id=item.attachment_id,
                        position=item.position,
                        attachment=attachment,
                    )
                )

            await session.execute(
                update(ChatParticipantModel)
                .where(ChatParticipantModel.chat_id == chat_id)
                .values(deleted_at=None)
            )
            await session.execute(
                update(ChatParticipantModel)
                .where(ChatParticipantModel.chat_id == chat_id)
                .where(ChatParticipantModel.user_id == sender_id)
                .values(last_seen_at=record.created_at)
            )
            await session.flush()
            return await cls.get_by_id(session, record.id)
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
    async def update(
        cls,
        session: AsyncSession,
        user_id: UUID,
        message_id: UUID,
        *,
        chat_id: UUID | None = None,
        message: str | None = None,
        attachments: list[AttachmentIdWithPositionRequest] | None = None,
    ) -> tuple[ChatMessageModel, list[str], list[str]]:
        record = await cls.get_by_id(session, message_id)
        if chat_id is not None and record.chat_id != chat_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat message not found",
            )

        await ChatRepository.assert_participant(
            session, record.chat_id, user_id
        )

        if record.sender_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can edit only your own messages",
            )

        old_object_keys: list[str] = []
        new_object_keys: list[str] = []
        attachment_records: dict[UUID, AttachmentModel] = {}
        if attachments is not None:
            old_object_keys = [
                link.attachment.object_key for link in record.attachment_links
            ]
            attachment_records = await cls._pending_attachments(
                session, user_id, attachments
            )
            new_object_keys = [
                attachment_records[item.attachment_id].object_key
                for item in attachments
            ]

        try:
            if message is not None:
                record.message = _clean_message(message)

            if attachments is not None:
                for link in list(record.attachment_links):
                    await session.delete(link.attachment)
                record.attachment_links.clear()
                await session.flush()

                for item in attachments:
                    attachment = attachment_records[item.attachment_id]
                    attachment.status = AttachmentStatus.ready
                    record.attachment_links.append(
                        ChatMessageAttachmentLink(
                            attachment_id=item.attachment_id,
                            position=item.position,
                            attachment=attachment,
                        )
                    )

            await session.flush()
            return (
                await cls.get_by_id(session, record.id),
                old_object_keys,
                new_object_keys,
            )
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ChatMessageRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chat message references invalid data",
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatMessageRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating chat message",
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
        if message.chat_id != chat_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat message not found",
            )
        await ChatRepository.assert_participant(session, chat_id, user_id)

        try:
            attachment_ids = await cls._attachment_ids(
                session, chat_id, message_id
            )
            if attachment_ids:
                await session.execute(
                    delete(AttachmentModel).where(
                        AttachmentModel.id.in_(attachment_ids)
                    )
                )
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
        cls, session: AsyncSession, message_id: UUID
    ) -> ChatMessageModel:
        stmt = (
            select(ChatMessageModel)
            .options(
                selectinload(ChatMessageModel.attachment_links).selectinload(
                    ChatMessageAttachmentLink.attachment
                )
            )
            .where(ChatMessageModel.id == message_id)
        )

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
        pagination: paginationDep,
    ) -> PaginatedResponse[ChatMessageResponse]:
        try:
            participant = await ChatRepository.assert_participant(
                session, chat_id, user_id
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
                    .options(
                        selectinload(
                            ChatMessageModel.attachment_links
                        ).selectinload(ChatMessageAttachmentLink.attachment)
                    )
                    .where(*filters)
                    .order_by(ChatMessageModel.created_at.desc())
                    .offset(pagination.offset)
                    .limit(pagination.limit)
                )
            ).all()

            return PaginatedResponse(
                data=[cls.to_response(record) for record in records],
                total=total,
            )
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"[ChatMessageRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving chat messages",
            )

    @classmethod
    async def attachment_keys(
        cls, session: AsyncSession, chat_id: UUID, message_id: UUID
    ) -> list[str]:
        try:
            return list(
                await session.scalars(
                    select(AttachmentModel.object_key)
                    .join(
                        ChatMessageAttachmentLink,
                        ChatMessageAttachmentLink.attachment_id
                        == AttachmentModel.id,
                    )
                    .join(
                        ChatMessageModel,
                        ChatMessageModel.id
                        == ChatMessageAttachmentLink.chat_message_id,
                    )
                    .where(
                        ChatMessageAttachmentLink.chat_message_id == message_id,
                        ChatMessageModel.id == message_id,
                        ChatMessageModel.chat_id == chat_id,
                    )
                )
            )
        except SQLAlchemyError as e:
            logger.error(f"[ChatMessageRepository] attachment_keys: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve message attachments",
            )

    @classmethod
    async def attachment_keys_until(
        cls, session: AsyncSession, chat_id: UUID, until: datetime
    ) -> list[str]:
        try:
            return list(
                await session.scalars(
                    select(AttachmentModel.object_key)
                    .join(
                        ChatMessageAttachmentLink,
                        ChatMessageAttachmentLink.attachment_id
                        == AttachmentModel.id,
                    )
                    .join(
                        ChatMessageModel,
                        ChatMessageModel.id
                        == ChatMessageAttachmentLink.chat_message_id,
                    )
                    .where(
                        ChatMessageModel.chat_id == chat_id,
                        ChatMessageModel.created_at <= until,
                    )
                )
            )
        except SQLAlchemyError as e:
            logger.error(f"[ChatMessageRepository] attachment_keys_until: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve message attachments",
            )

    @classmethod
    async def delete_until(
        cls, session: AsyncSession, chat_id: UUID, until: datetime
    ) -> None:
        try:
            attachment_ids = await cls._attachment_ids_until(
                session, chat_id, until
            )
            if attachment_ids:
                await session.execute(
                    delete(AttachmentModel).where(
                        AttachmentModel.id.in_(attachment_ids)
                    )
                )
            await session.execute(
                delete(ChatMessageModel).where(
                    ChatMessageModel.chat_id == chat_id,
                    ChatMessageModel.created_at <= until,
                )
            )
            await session.flush()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatMessageRepository] delete_until: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting chat messages",
            )

    @staticmethod
    def to_response(record: ChatMessageModel) -> ChatListLastMessageResponse:
        return ChatListLastMessageResponse(
            id=record.id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            sender_id=record.sender_id,
            message=record.message,
            chat_id=record.chat_id,
            reply_id=record.reply_id,
            attachments=[
                AttachmentWithPositionResponse(
                    id=link.attachment.id,
                    object_key=link.attachment.object_key,
                    original_filename=link.attachment.original_filename,
                    status=link.attachment.status,
                    mime_type=link.attachment.mime_type,
                    label=link.attachment.label,
                    group=link.attachment.group,
                    size_bytes=link.attachment.size_bytes,
                    meta=link.attachment.meta,
                    position=link.position,
                )
                for link in record.attachment_links
            ],
            seen_by_recipient=False,
        )

    @staticmethod
    async def _assert_reply_belongs_to_chat(
        session: AsyncSession, chat_id: UUID, reply_id: UUID
    ) -> None:
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

    @staticmethod
    async def _pending_attachments(
        session: AsyncSession,
        owner_id: UUID,
        attachments: list[AttachmentIdWithPositionRequest],
    ) -> dict[UUID, AttachmentModel]:
        if not attachments:
            return {}

        attachment_ids = [item.attachment_id for item in attachments]
        if len(attachment_ids) != len(set(attachment_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="attachment ids must be unique",
            )

        records = (
            await session.scalars(
                select(AttachmentModel).where(
                    AttachmentModel.id.in_(attachment_ids),
                    AttachmentModel.owner_id == owner_id,
                    AttachmentModel.status == AttachmentStatus.pending,
                )
            )
        ).all()
        if len(records) != len(attachment_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or already attached attachment",
            )

        return {record.id: record for record in records}

    @staticmethod
    async def _attachment_ids(
        session: AsyncSession, chat_id: UUID, message_id: UUID
    ) -> list[UUID]:
        return list(
            await session.scalars(
                select(AttachmentModel.id)
                .join(
                    ChatMessageAttachmentLink,
                    ChatMessageAttachmentLink.attachment_id
                    == AttachmentModel.id,
                )
                .join(
                    ChatMessageModel,
                    ChatMessageModel.id
                    == ChatMessageAttachmentLink.chat_message_id,
                )
                .where(
                    ChatMessageModel.chat_id == chat_id,
                    ChatMessageModel.id == message_id,
                )
            )
        )

    @staticmethod
    async def _attachment_ids_until(
        session: AsyncSession, chat_id: UUID, until: datetime
    ) -> list[UUID]:
        return list(
            await session.scalars(
                select(AttachmentModel.id)
                .join(
                    ChatMessageAttachmentLink,
                    ChatMessageAttachmentLink.attachment_id
                    == AttachmentModel.id,
                )
                .join(
                    ChatMessageModel,
                    ChatMessageModel.id
                    == ChatMessageAttachmentLink.chat_message_id,
                )
                .where(
                    ChatMessageModel.chat_id == chat_id,
                    ChatMessageModel.created_at <= until,
                )
            )
        )


def _clean_message(message: str | None) -> str | None:
    if message is None:
        return None
    text = message.strip()
    return text or None
