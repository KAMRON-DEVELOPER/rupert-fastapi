from uuid import UUID

from fastapi import Query

from src.apps.shared.schemas import MessageResponse
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.schemas.session import SessionResponse
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(auth: authDep, session: sessionDep):
    user_id, _, _ = auth
    records = await SessionsRepository.list_by_user_id(session, user_id)
    return [SessionResponse.model_validate(record) for record in records]


@users_router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(auth: authDep, session: sessionDep, session_id: UUID):
    user_id, _, _ = auth
    await SessionsRepository.delete_by_id(session, user_id, session_id)
    await session.commit()
    return MessageResponse(message="Session revoked successfully")


@users_router.delete("/sessions", response_model=MessageResponse)
async def revoke_sessions(
    auth: authDep,
    session: sessionDep,
    include_current: bool = Query(default=False),
):
    user_id, _, refresh_token = auth
    except_refresh_token = None if include_current else refresh_token
    deleted_count = await SessionsRepository.delete_all_by_user_id(
        session, user_id, except_refresh_token=except_refresh_token
    )
    await session.commit()
    return MessageResponse(message=f"Revoked {deleted_count} sessions")
