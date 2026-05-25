# from dataclasses import dataclass
# from datetime import UTC, datetime
# from uuid import UUID

# from fastapi import HTTPException, status
# from sqlalchemy import and_, delete, func, literal, or_, select, update
# from sqlalchemy.exc import IntegrityError, SQLAlchemyError
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import aliased

# from src.apps.chats.models import (
#     ChatMessageModel,
#     ChatModel,
#     ChatParticipantModel,
# )
# from src.apps.chats.schemas.chat import ChatListItemResponse
# from src.apps.chats.schemas.chat_message import ChatListLastMessageResponse
# from src.apps.chats.schemas.chat_participant import ChatListUserResponse
# from src.apps.shared.schemas import PaginatedResponse
# from src.apps.users.models import UserModel
# from src.core.logger import logger


# @dataclass(frozen=True, slots=True)
# class ChatListRow:
#     chat_id: UUID

#     is_pinned: bool
#     is_muted: bool

#     other_user_id: UUID
#     other_user_first_name: str
#     other_user_last_name: str | None
#     other_user_avatar_url: str | None

#     other_last_seen_at: datetime | None

#     latest_message_id: UUID | None
#     latest_message_sender_id: UUID | None
#     latest_message_created_at: datetime | None
#     latest_message_text: str | None
#     latest_message_image_urls: list[str] | None
#     latest_message_video_urls: list[str] | None
#     latest_message_reply_id: UUID | None

#     unread_count: int


# @dataclass(frozen=True, slots=True)
# class ChatListPage:
#     data: list[ChatListRow]
#     total: int


# class ChatRepository:
#     @staticmethod
#     def _preview(
#         message: str | None, image_count: int, video_count: int
#     ) -> str:
#         text = (message or "").strip()
#         if text:
#             return text
#         if image_count and video_count:
#             return f"{image_count + video_count} media"
#         if image_count == 1:
#             return "Photo"
#         if image_count > 1:
#             return f"{image_count} photos"
#         if video_count == 1:
#             return "Video"
#         if video_count > 1:
#             return f"{video_count} videos"
#         return ""

#     @classmethod
#     async def delete(cls, session: AsyncSession, chat_id: UUID) -> UUID:
#         stmt = (
#             delete(ChatModel)
#             .where(ChatModel.id == chat_id)
#             .returning(ChatModel.id)
#         )

#         try:
#             deleted_id = await session.scalar(stmt)

#             if not deleted_id:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail="Chat not found",
#                 )

#             return deleted_id
#         except HTTPException:
#             raise
#         except SQLAlchemyError as e:
#             await session.rollback()
#             logger.error(f"[ChatRepository] delete: {e}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Something went wrong while deleting chat",
#             )

#     @classmethod
#     async def get_or_create_direct_chat(
#         cls, session: AsyncSession, current_user_id: UUID, other_user_id: UUID
#     ) -> ChatModel:
#         if current_user_id == other_user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="You cannot create a chat with yourself",
#             )

#         other_exists = await session.scalar(
#             select(UserModel.id).where(UserModel.id == other_user_id)
#         )
#         if not other_exists:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#             )

#         candidate_chat_ids = (
#             select(ChatParticipantModel.chat_id)
#             .where(
#                 ChatParticipantModel.user_id.in_(
#                     [current_user_id, other_user_id]
#                 )
#             )
#             .group_by(ChatParticipantModel.chat_id)
#             .having(
#                 func.count(func.distinct(ChatParticipantModel.user_id)) == 2
#             )
#             .subquery()
#         )

#         existing_chat = await session.scalar(
#             select(ChatModel)
#             .join(
#                 ChatParticipantModel,
#                 ChatParticipantModel.chat_id == ChatModel.id,
#             )
#             .where(ChatModel.id.in_(select(candidate_chat_ids.c.chat_id)))
#             .group_by(ChatModel.id)
#             .having(func.count(ChatParticipantModel.id) == 2)
#             .limit(1)
#         )

#         if existing_chat:
#             await session.execute(
#                 update(ChatParticipantModel)
#                 .where(ChatParticipantModel.chat_id == existing_chat.id)
#                 .where(
#                     ChatParticipantModel.user_id.in_(
#                         [current_user_id, other_user_id]
#                     )
#                 )
#                 .values(deleted_at=None)
#             )
#             await session.flush()
#             return existing_chat

#         chat = ChatModel()
#         session.add(chat)
#         await session.flush()

#         session.add_all(
#             [
#                 ChatParticipantModel(chat_id=chat.id, user_id=current_user_id),
#                 ChatParticipantModel(chat_id=chat.id, user_id=other_user_id),
#             ]
#         )

#         try:
#             await session.flush()
#             return chat
#         except IntegrityError as e:
#             await session.rollback()
#             logger.error(
#                 f"[ChatRepository] get_or_create_direct_chat integrity: {e}"
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Could not create direct chat",
#             )
#         except SQLAlchemyError as e:
#             await session.rollback()
#             logger.error(f"[ChatRepository] get_or_create_direct_chat: {e}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Something went wrong while creating direct chat",
#             )

#     @classmethod
#     async def assert_participant(
#         cls, session: AsyncSession, chat_id: UUID, user_id: UUID
#     ) -> ChatParticipantModel:
#         participant = await session.scalar(
#             select(ChatParticipantModel).where(
#                 ChatParticipantModel.chat_id == chat_id,
#                 ChatParticipantModel.user_id == user_id,
#             )
#         )
#         if not participant:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
#             )
#         return participant

#     @classmethod
#     async def get_many(
#         cls, session: AsyncSession, user_id: UUID, offset: int, limit: int
#     ) -> PaginatedResponse[ChatListItemResponse]:
#         epoch = datetime(1970, 1, 1, tzinfo=UTC)

#         CurrentForLatest = aliased(ChatParticipantModel)
#         CurrentForUnread = aliased(ChatParticipantModel)
#         OtherParticipant = aliased(ChatParticipantModel)

#         visible_filter = and_(
#             ChatParticipantModel.user_id == user_id,
#             ChatParticipantModel.deleted_at.is_(None),
#             ChatParticipantModel.is_archived.is_(False),
#         )

#         total_stmt = (
#             select(func.count(ChatModel.id))
#             .join(
#                 ChatParticipantModel,
#                 ChatParticipantModel.chat_id == ChatModel.id,
#             )
#             .where(visible_filter)
#         )

#         latest_messages_stmt = (
#             select(
#                 ChatMessageModel.id.label("id"),
#                 ChatMessageModel.created_at.label("created_at"),
#                 ChatMessageModel.updated_at.label("updated_at"),
#                 ChatMessageModel.sender_id.label("sender_id"),
#                 ChatMessageModel.message.label("message"),
#                 ChatMessageModel.image_urls.label("image_urls"),
#                 ChatMessageModel.video_urls.label("video_urls"),
#                 ChatMessageModel.chat_id.label("chat_id"),
#                 ChatMessageModel.reply_id.label("reply_id"),
#                 func.row_number()
#                 .over(
#                     partition_by=ChatMessageModel.chat_id,
#                     order_by=ChatMessageModel.updated_at.desc(),
#                 )
#                 .label("rn"),
#             )
#             .join(
#                 CurrentForLatest,
#                 and_(
#                     CurrentForLatest.chat_id == ChatMessageModel.chat_id,
#                     CurrentForLatest.user_id == user_id,
#                 ),
#             )
#             .where(
#                 or_(
#                     CurrentForLatest.cleared_at.is_(None),
#                     ChatMessageModel.created_at > CurrentForLatest.cleared_at,
#                 )
#             )
#             .subquery()
#         )

#         unread_counts_stmt = (
#             select(
#                 ChatMessageModel.chat_id.label("chat_id"),
#                 func.count(ChatMessageModel.id).label("unread_count"),
#             )
#             .join(
#                 CurrentForUnread,
#                 and_(
#                     CurrentForUnread.chat_id == ChatMessageModel.chat_id,
#                     CurrentForUnread.user_id == user_id,
#                 ),
#             )
#             .where(
#                 ChatMessageModel.sender_id != user_id,
#                 ChatMessageModel.created_at
#                 > func.coalesce(CurrentForUnread.last_seen_at, literal(epoch)),
#                 or_(
#                     CurrentForUnread.cleared_at.is_(None),
#                     ChatMessageModel.created_at > CurrentForUnread.cleared_at,
#                 ),
#             )
#             .group_by(ChatMessageModel.chat_id)
#             .subquery()
#         )

#         data_stmt = (
#             select(
#                 ChatModel.id.label("chat_id"),
#                 ChatParticipantModel.is_pinned,
#                 ChatParticipantModel.is_muted,
#                 ChatParticipantModel.is_archived,
#                 UserModel.id.label("other_user_id"),
#                 UserModel.first_name.label("other_first_name"),
#                 UserModel.last_name.label("other_last_name"),
#                 UserModel.avatar_url.label("other_avatar_url"),
#                 OtherParticipant.last_seen_at.label("other_last_seen_at"),
#                 latest_messages_stmt.c.id.label("last_message_id"),
#                 latest_messages_stmt.c.sender_id.label("last_sender_id"),
#                 latest_messages_stmt.c.created_at.label("last_created_at"),
#                 latest_messages_stmt.c.updated_at.label("last_updated_at"),
#                 latest_messages_stmt.c.message.label("last_message"),
#                 latest_messages_stmt.c.image_urls.label("last_image_urls"),
#                 latest_messages_stmt.c.video_urls.label("last_video_urls"),
#                 latest_messages_stmt.c.reply_id.label("last_reply_id"),
#                 func.coalesce(unread_counts_stmt.c.unread_count, 0).label(
#                     "unread_count"
#                 ),
#             )
#             .join(
#                 ChatParticipantModel,
#                 and_(
#                     ChatParticipantModel.chat_id == ChatModel.id,
#                     ChatParticipantModel.user_id == user_id,
#                 ),
#             )
#             .join(
#                 OtherParticipant,
#                 and_(
#                     OtherParticipant.chat_id == ChatModel.id,
#                     OtherParticipant.user_id != user_id,
#                 ),
#             )
#             .join(UserModel, UserModel.id == OtherParticipant.user_id)
#             .outerjoin(
#                 latest_messages_stmt,
#                 and_(
#                     latest_messages_stmt.c.chat_id == ChatModel.id,
#                     latest_messages_stmt.c.rn == 1,
#                 ),
#             )
#             .outerjoin(
#                 unread_counts_stmt, unread_counts_stmt.c.chat_id == ChatModel.id
#             )
#             .where(ChatParticipantModel.deleted_at.is_(None))
#             .where(ChatParticipantModel.is_archived.is_(False))
#             .order_by(
#                 ChatParticipantModel.is_pinned.desc(),
#                 latest_messages_stmt.c.created_at.desc().nulls_last(),
#                 ChatModel.created_at.desc(),
#             )
#             .offset(offset)
#             .limit(limit)
#         )

#         try:
#             total = await session.scalar(total_stmt) or 0
#             rows = (await session.execute(data_stmt)).all()
#         except SQLAlchemyError as e:
#             logger.error(f"[ChatRepository] get_many: {e}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Could not retrieve chat list",
#             )

#         items: list[ChatListItemResponse] = []
#         for row in rows:
#             last_message = None
#             if row.last_message_id and row.last_created_at:
#                 image_count = len(row.last_image_urls or [])
#                 video_count = len(row.last_video_urls or [])
#                 is_mine = row.last_sender_id == user_id
#                 last_message = ChatListLastMessageResponse(
#                     id=row.last_message_id,
#                     sender_id=row.last_sender_id,
#                     created_at=row.last_created_at,
#                     updated_at=row.last_updated_at,
#                     reply_id=row.last_reply_id,
#                     message=row.last_message,
#                     image_count=image_count,
#                     video_count=video_count,
#                     media_count=image_count + video_count,
#                     preview=cls._preview(
#                         row.last_message, image_count, video_count
#                     ),
#                     is_mine=is_mine,
#                     seen_by_other=(
#                         row.other_last_seen_at is not None
#                         and row.other_last_seen_at >= row.last_created_at
#                         if is_mine
#                         else None
#                     ),
#                 )

#             items.append(
#                 ChatListItemResponse(
#                     id=row.chat_id,
#                     user=ChatListUserResponse(
#                         id=row.other_user_id,
#                         first_name=row.other_first_name,
#                         last_name=row.other_last_name,
#                         avatar_url=row.other_avatar_url,
#                     ),
#                     is_pinned=row.is_pinned,
#                     is_muted=row.is_muted,
#                     is_archived=row.is_archived,
#                     last_message=last_message,
#                     unread_count=row.unread_count,
#                 )
#             )

#         return PaginatedResponse(data=items, total=total)
