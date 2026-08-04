from typing import Annotated

from fastapi import Query, status

from src.apps.chats.schemas.chat_participant import ChatListUserResponse
from src.apps.shared.schemas import (
    MessageResponse,
    PaginatedResponse,
    paginationDep,
)
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas.user import (
    UserDetailResponse,
    UserSummaryResponse,
    UserUpdateRequest,
)
from src.core.boto3 import delete_objects_from_boto3, wipe_objects_from_boto3
from src.core.database import sessionDep
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import authDep

from .router import users_router

settings = get_settings()


@users_router.get(
    "/search", response_model=PaginatedResponse[ChatListUserResponse]
)
async def search_users(
    session: sessionDep,
    pagination: paginationDep,
    q: Annotated[str | None, Query(min_length=1)] = None,
):
    return await UsersRepository.search(
        session, query=q, limit=pagination.limit, offset=pagination.offset
    )


@users_router.get("/", response_model=UserDetailResponse | UserSummaryResponse)
async def get_user(
    auth: authDep,
    session: sessionDep,
    summary: Annotated[bool, Query()] = False,
):
    user_id, _, _ = auth

    if summary:
        user = await UsersRepository.get_summary(session, user_id)
        return UserSummaryResponse.model_validate(user)
    else:
        user = await UsersRepository.get_detail(
            session, user_id, current_user_id=user_id
        )
        return UserDetailResponse.model_validate(user)


@users_router.patch("/", response_model=MessageResponse)
async def update_user(
    auth: authDep, session: sessionDep, schm: UserUpdateRequest
):
    user_id, _, _ = auth

    values = schm.model_dump(exclude_unset=True)

    if schm.delete_avatar_key:
        await delete_objects_from_boto3([schm.delete_avatar_key])
        values["avatar_url"] = None

    if schm.delete_banner_key:
        await delete_objects_from_boto3([schm.delete_banner_key])
        values["banner_url"] = None

    await UsersRepository.update(session, user_id, values)
    await session.commit()
    return MessageResponse(message="User updated successfully")


@users_router.delete(
    "/", response_model=None, status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(auth: authDep, session: sessionDep):
    user_id, _, refresh_token = auth

    await SessionsRepository.delete(session, user_id, refresh_token)
    await UsersRepository.delete(session, user_id)
    await session.commit()

    await wipe_objects_from_boto3(user_id=user_id.hex)
