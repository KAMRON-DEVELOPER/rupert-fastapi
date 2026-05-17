from uuid import UUID

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.repositories.session import SessionsRepository
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import create_token, set_cookie

settings = get_settings()


async def finalize_session(
    req: Request, res: Response, user_id: UUID, session: AsyncSession
):
    try:
        user_agent = req.headers.get("user-agent", "unknown")
        ip_addr = req.client.host if req.client else "unknown"

        new_access_token = create_token(user_id=user_id, type="access")
        new_refresh_token = create_token(user_id=user_id, type="refresh")

        set_cookie(
            res,
            key="access_token",
            value=new_access_token,
            max_age=settings.jwt.access_token_expire_in_minutes * 60,
        )
        set_cookie(
            res,
            key="refresh_token",
            value=new_refresh_token,
            max_age=settings.jwt.refresh_token_expire_in_days * 86400,
        )

        await SessionsRepository.create(
            session,
            new_refresh_token,
            user_id,
            user_agent=user_agent,
            ip_addr=ip_addr,
            device_name="",
        )
    except HTTPException as e:
        raise e
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while finalizing session",
        )
