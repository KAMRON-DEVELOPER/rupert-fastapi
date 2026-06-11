from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, literal, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from src.apps.chats.models import (
    ChatMessageAttachmentLink,
    ChatMessageModel,
    ChatModel,
    ChatParticipantModel,
)
from src.apps.chats.schemas.chat import ChatListItemResponse
from src.apps.chats.schemas.chat_message import ChatListLastMessageResponse
from src.apps.chats.schemas.chat_participant import ChatListUserResponse
from src.apps.shared.models.attachment import AttachmentModel
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.apps.shared.schemas.attachment import AttachmentWithPositionResponse
from src.apps.users.models import UserModel
from src.core.logger import logger


class ChatRepository:
    @classmethod
    async def get_or_create_direct_chat(
        cls, session: AsyncSession, user_id: UUID, participant_id: UUID
    ) -> ChatModel:
        if user_id == participant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot create a chat with yourself",
            )

        other_exists = await session.scalar(
            select(UserModel.id).where(UserModel.id == participant_id)
        )
        if not other_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        candidate_chat_ids = (
            select(ChatParticipantModel.chat_id)
            .where(ChatParticipantModel.user_id.in_([user_id, participant_id]))
            .group_by(ChatParticipantModel.chat_id)
            .having(
                func.count(func.distinct(ChatParticipantModel.user_id)) == 2
            )
            .subquery()
        )

        existing_chat = await session.scalar(
            select(ChatModel)
            .join(
                ChatParticipantModel,
                ChatParticipantModel.chat_id == ChatModel.id,
            )
            .where(ChatModel.id.in_(select(candidate_chat_ids.c.chat_id)))
            .group_by(ChatModel.id)
            .having(func.count(ChatParticipantModel.id) == 2)
            .limit(1)
        )

        if existing_chat:
            await session.execute(
                update(ChatParticipantModel)
                .where(ChatParticipantModel.chat_id == existing_chat.id)
                .where(
                    ChatParticipantModel.user_id.in_([user_id, participant_id])
                )
                .values(deleted_at=None)
            )
            await session.flush()
            return existing_chat

        chat = ChatModel()
        session.add(chat)
        await session.flush()

        session.add_all(
            [
                ChatParticipantModel(chat_id=chat.id, user_id=user_id),
                ChatParticipantModel(chat_id=chat.id, user_id=participant_id),
            ]
        )

        try:
            await session.flush()
            return chat
        except IntegrityError as e:
            await session.rollback()
            logger.error(
                f"[ChatRepository] get_or_create_direct_chat integrity: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Could not create direct chat",
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatRepository] get_or_create_direct_chat: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating direct chat",
            )

    @classmethod
    async def assert_participant(
        cls, session: AsyncSession, chat_id: UUID, user_id: UUID
    ) -> ChatParticipantModel:
        try:
            participant = await session.scalar(
                select(ChatParticipantModel).where(
                    ChatParticipantModel.chat_id == chat_id,
                    ChatParticipantModel.user_id == user_id,
                )
            )
        except SQLAlchemyError as e:
            logger.error(f"[ChatRepository] assert_participant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while checking chat access",
            )

        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )
        return participant

    @classmethod
    async def get_list_item(
        cls, session: AsyncSession, chat_id: UUID, user_id: UUID
    ) -> ChatListItemResponse:
        current = await session.scalar(
            select(ChatParticipantModel).where(
                ChatParticipantModel.chat_id == chat_id,
                ChatParticipantModel.user_id == user_id,
                ChatParticipantModel.deleted_at.is_(None),
            )
        )
        if not current:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        other = await session.scalar(
            select(ChatParticipantModel).where(
                ChatParticipantModel.chat_id == chat_id,
                ChatParticipantModel.user_id != user_id,
            )
        )
        if not other:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat participant not found",
            )

        other_user = await session.scalar(
            select(UserModel).where(UserModel.id == other.user_id)
        )
        if not other_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        last_message = await session.scalar(
            select(ChatMessageModel)
            .options(
                selectinload(ChatMessageModel.attachment_links).selectinload(
                    ChatMessageAttachmentLink.attachment
                )
            )
            .where(ChatMessageModel.chat_id == chat_id)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(1)
        )

        conditions = [
            ChatMessageModel.chat_id == chat_id,
            ChatMessageModel.sender_id != user_id,
        ]

        if current.last_seen_at is not None:
            conditions.append(
                ChatMessageModel.created_at > current.last_seen_at
            )

        if current.cleared_at is not None:
            conditions.append(ChatMessageModel.created_at > current.cleared_at)

        unread_count = (
            await session.scalar(
                select(func.count(ChatMessageModel.id)).where(*conditions)
            )
            or 0
        )

        last_message_response = None
        if last_message is not None:
            seen_by_recipient = None
            if last_message.sender_id == user_id:
                seen_by_recipient = (
                    other.last_seen_at is not None
                    and other.last_seen_at >= last_message.created_at
                )
            last_message_response = cls._last_message_response(
                last_message, seen_by_recipient=seen_by_recipient
            )

        return ChatListItemResponse(
            id=chat_id,
            created_at=current.created_at,
            updated_at=current.updated_at,
            user=ChatListUserResponse(
                id=other_user.id,
                first_name=other_user.first_name,
                last_name=other_user.last_name,
                avatar_url=other_user.avatar_url,
            ),
            is_pinned=current.is_pinned,
            is_muted=current.is_muted,
            is_archived=current.is_archived,
            last_message=last_message_response,
            unread_count=unread_count,
        )

    @classmethod
    async def get_participant_ids(
        cls, session: AsyncSession, user_id: UUID
    ) -> Sequence[UUID]:
        user = aliased(ChatParticipantModel)
        participant = aliased(ChatParticipantModel)

        stmt = (
            select(participant.user_id)
            .distinct()
            .select_from(user)
            .join(participant, participant.chat_id == user.chat_id)
            .where(
                user.user_id == user_id,
                participant.user_id != user_id,
                participant.deleted_at.is_(None),
            )
        )

        try:
            return (await session.scalars(stmt)).all()
        except SQLAlchemyError as e:
            logger.error(f"[ChatRepository] get_participant_ids: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve chat participants",
            )

    @classmethod
    async def get_many(
        cls, session: AsyncSession, user_id: UUID, pagination: paginationDep
    ) -> PaginatedResponse[ChatListItemResponse]:
        epoch = datetime(1970, 1, 1, tzinfo=UTC)
        current_for_latest = aliased(ChatParticipantModel)
        current_for_unread = aliased(ChatParticipantModel)
        other_participant = aliased(ChatParticipantModel)

        visible_filter = and_(
            ChatParticipantModel.user_id == user_id,
            ChatParticipantModel.deleted_at.is_(None),
            ChatParticipantModel.is_archived.is_(False),
        )

        total_stmt = select(func.count(ChatParticipantModel.id)).where(
            visible_filter
        )

        latest_messages = (
            select(
                ChatMessageModel.id.label("id"),
                ChatMessageModel.chat_id.label("chat_id"),
                ChatMessageModel.created_at.label("created_at"),
                func.row_number()
                .over(
                    partition_by=ChatMessageModel.chat_id,
                    order_by=ChatMessageModel.created_at.desc(),
                )
                .label("rn"),
            )
            .join(
                current_for_latest,
                and_(
                    current_for_latest.chat_id == ChatMessageModel.chat_id,
                    current_for_latest.user_id == user_id,
                ),
            )
            .where(
                or_(
                    current_for_latest.cleared_at.is_(None),
                    ChatMessageModel.created_at > current_for_latest.cleared_at,
                )
            )
            .subquery()
        )

        unread_counts = (
            select(
                ChatMessageModel.chat_id.label("chat_id"),
                func.count(ChatMessageModel.id).label("unread_count"),
            )
            .join(
                current_for_unread,
                and_(
                    current_for_unread.chat_id == ChatMessageModel.chat_id,
                    current_for_unread.user_id == user_id,
                ),
            )
            .where(
                ChatMessageModel.sender_id != user_id,
                ChatMessageModel.created_at
                > func.coalesce(
                    current_for_unread.last_seen_at, literal(epoch)
                ),
                or_(
                    current_for_unread.cleared_at.is_(None),
                    ChatMessageModel.created_at > current_for_unread.cleared_at,
                ),
            )
            .group_by(ChatMessageModel.chat_id)
            .subquery()
        )

        data_stmt = (
            select(
                ChatModel.id.label("chat_id"),
                ChatParticipantModel.is_pinned,
                ChatParticipantModel.is_muted,
                ChatParticipantModel.is_archived,
                UserModel.id.label("other_user_id"),
                UserModel.first_name.label("other_first_name"),
                UserModel.last_name.label("other_last_name"),
                UserModel.avatar_url.label("other_avatar_url"),
                other_participant.last_seen_at.label("other_last_seen_at"),
                latest_messages.c.id.label("last_message_id"),
                func.coalesce(unread_counts.c.unread_count, 0).label(
                    "unread_count"
                ),
            )
            .join(ChatModel, ChatModel.id == ChatParticipantModel.chat_id)
            .join(
                other_participant,
                and_(
                    other_participant.chat_id == ChatModel.id,
                    other_participant.user_id != user_id,
                ),
            )
            .join(UserModel, UserModel.id == other_participant.user_id)
            .outerjoin(
                latest_messages,
                and_(
                    latest_messages.c.chat_id == ChatModel.id,
                    latest_messages.c.rn == 1,
                ),
            )
            .outerjoin(unread_counts, unread_counts.c.chat_id == ChatModel.id)
            .where(visible_filter)
            .order_by(
                ChatParticipantModel.is_pinned.desc(),
                latest_messages.c.created_at.desc().nulls_last(),
                ChatModel.created_at.desc(),
            )
            .offset(pagination.offset)
            .limit(pagination.limit)
        )

        try:
            total = await session.scalar(total_stmt) or 0
            rows = (await session.execute(data_stmt)).all()
        except SQLAlchemyError as e:
            logger.error(f"[ChatRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve chat list",
            )

        last_message_ids = [
            row.last_message_id for row in rows if row.last_message_id
        ]
        last_messages = await cls._messages_by_id(session, last_message_ids)

        items: list[ChatListItemResponse] = []
        for row in rows:
            message = last_messages.get(row.last_message_id)
            last_message = None
            if message is not None:
                seen_by_recipient = None
                if message.sender_id == user_id:
                    seen_by_recipient = (
                        row.other_last_seen_at is not None
                        and row.other_last_seen_at >= message.created_at
                    )
                last_message = cls._last_message_response(
                    message, seen_by_recipient=seen_by_recipient
                )

            items.append(
                ChatListItemResponse(
                    id=row.chat_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    user=ChatListUserResponse(
                        id=row.other_user_id,
                        first_name=row.other_first_name,
                        last_name=row.other_last_name,
                        avatar_url=row.other_avatar_url,
                    ),
                    is_pinned=row.is_pinned,
                    is_muted=row.is_muted,
                    is_archived=row.is_archived,
                    last_message=last_message,
                    unread_count=row.unread_count,
                )
            )

        return PaginatedResponse(data=items, total=total)

    @classmethod
    async def attachment_keys(
        cls, session: AsyncSession, chat_id: UUID
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
                    .where(ChatMessageModel.chat_id == chat_id)
                )
            )
        except SQLAlchemyError as e:
            logger.error(f"[ChatRepository] attachment_keys: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve chat attachments",
            )

    @classmethod
    async def delete_for_everyone(
        cls, session: AsyncSession, chat_id: UUID, user_id: UUID
    ) -> None:
        await cls.assert_participant(session, chat_id, user_id)
        try:
            attachment_ids = await cls._attachment_ids(session, chat_id)
            if attachment_ids:
                await session.execute(
                    delete(AttachmentModel).where(
                        AttachmentModel.id.in_(attachment_ids)
                    )
                )
            deleted_id = await session.scalar(
                delete(ChatModel)
                .where(ChatModel.id == chat_id)
                .returning(ChatModel.id)
            )
            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat not found",
                )
            await session.flush()
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"[ChatRepository] delete_for_everyone: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting chat",
            )

    @staticmethod
    async def _messages_by_id(
        session: AsyncSession, message_ids: list[UUID]
    ) -> dict[UUID, ChatMessageModel]:
        if not message_ids:
            return {}

        records = (
            await session.scalars(
                select(ChatMessageModel)
                .options(
                    selectinload(
                        ChatMessageModel.attachment_links
                    ).selectinload(ChatMessageAttachmentLink.attachment)
                )
                .where(ChatMessageModel.id.in_(message_ids))
            )
        ).all()
        return {record.id: record for record in records}

    @staticmethod
    def _last_message_response(
        message: ChatMessageModel, *, seen_by_recipient: bool | None
    ) -> ChatListLastMessageResponse:
        return ChatListLastMessageResponse(
            id=message.id,
            created_at=message.created_at,
            updated_at=message.updated_at,
            sender_id=message.sender_id,
            message=message.message,
            chat_id=message.chat_id,
            reply_id=message.reply_id,
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
                for link in message.attachment_links
            ],
            seen_by_recipient=seen_by_recipient,
        )

    @staticmethod
    async def _attachment_ids(
        session: AsyncSession, chat_id: UUID
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
                .where(ChatMessageModel.chat_id == chat_id)
            )
        )
