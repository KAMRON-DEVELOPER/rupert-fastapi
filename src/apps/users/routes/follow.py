from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse, PaginatedResponse
from src.apps.shared.schemas.enums import FollowStatus
from src.apps.shared.schemas.pagination import paginationDep
from src.apps.users.repositories.follow import FollowsRepository
from src.apps.users.schemas.follow import FollowResponse, FollowUpdateRequest
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.post(
    "/{following_id}/follow",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def follow(auth: authDep, session: sessionDep, following_id: UUID):
    user_id, _, _ = auth

    record = await FollowsRepository.follow(session, user_id, following_id)
    await session.commit()
    return FollowResponse.model_validate(record)


@users_router.delete(
    "/{following_id}/follow",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def unfollow_(auth: authDep, session: sessionDep, following_id: UUID):
    user_id, _, _ = auth

    await FollowsRepository.unfollow(session, user_id, following_id)
    await session.commit()
    return MessageResponse(message="User unfollowed successfully")


@users_router.get(
    "/followers", response_model=PaginatedResponse[FollowResponse]
)
async def list_followers(
    auth: authDep, session: sessionDep, pagination: paginationDep
):
    user_id, _, _ = auth

    return await FollowsRepository.list_followers(session, user_id, pagination)


@users_router.get(
    "/following", response_model=PaginatedResponse[FollowResponse]
)
async def list_following(
    auth: authDep, session: sessionDep, pagination: paginationDep
):
    user_id, _, _ = auth

    return await FollowsRepository.list_following(session, user_id, pagination)


@users_router.get(
    "/follow-requests", response_model=PaginatedResponse[FollowResponse]
)
async def list_follow_requests(
    auth: authDep, session: sessionDep, pagination: paginationDep
):
    user_id, _, _ = auth
    return await FollowsRepository.list_pending_requests(
        session, user_id, pagination
    )


@users_router.patch(
    "/follow-requests/{follow_id}", response_model=FollowResponse
)
async def update_follow_request(
    auth: authDep,
    session: sessionDep,
    follow_id: UUID,
    schm: FollowUpdateRequest,
):
    user_id, _, _ = auth
    record = await FollowsRepository.update_request_status(
        session, user_id, follow_id, FollowStatus(schm.status)
    )
    await session.commit()
    return FollowResponse.model_validate(record)
