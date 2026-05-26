from uuid import UUID

from src.apps.chats.repositories.chat_message import ChatMessageRepository
from src.apps.chats.schemas.chat_message import ChatMessageResponse
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import chats_router


@chats_router.get(
    "/{chat_id}/messages", response_model=PaginatedResponse[ChatMessageResponse]
)
async def list_chat_messages(
    auth: authDep, session: sessionDep, pagination: paginationDep, chat_id: UUID
):
    user_id, _, _ = auth
    return await ChatMessageRepository.get_many(
        session, chat_id, user_id, pagination
    )
