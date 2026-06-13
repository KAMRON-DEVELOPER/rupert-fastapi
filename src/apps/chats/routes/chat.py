from src.apps.chats.repositories.chat import ChatRepository
from src.apps.chats.schemas.chat import ChatListItemResponse
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.core.database import sessionDep
from src.core.websocket.presence import presence
from src.core.websocket.types import UserId
from src.dependencies.proactive_refresh import authDep

from .router import chats_router


@chats_router.get("/", response_model=PaginatedResponse[ChatListItemResponse])
async def list_chats(
    auth: authDep, session: sessionDep, pagination: paginationDep
):
    user_id, _, _ = auth
    result = await ChatRepository.get_many(session, user_id, pagination)

    user_ids = [UserId(str(item.user.id)) for item in result.data]
    online_map = await presence.are_online(user_ids)
    for item in result.data:
        item.user.is_online = online_map.get(UserId(str(item.user.id)), False)

    return result
