from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.schemas.chat import ChatListItemResponse
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import chats_router


@chats_router.get("/", response_model=PaginatedResponse[ChatListItemResponse])
async def list_chats(
    auth: authDep, session: sessionDep, pagination: paginationDep
):
    user_id, _, _ = auth
    return await ChatRepository.get_many(session, user_id, pagination)
