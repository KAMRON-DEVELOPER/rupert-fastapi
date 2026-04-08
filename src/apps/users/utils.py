from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.proactive_refresh import create_token
from src.apps.models import UserModel
from src.apps.users.repositories.session import SessionsRepository
from src.utils.settings import get_settings

settings = get_settings()


async def finalize_session(
    user: UserModel,
    req: Request,
    res: Response,
    session: AsyncSession,
) -> UserModel:
    user_agent = req.headers.get("user-agent", "")
    ip_addr = req.client.host if req.client else ""

    access_token = create_token(user_id=user.id, type="access")
    refresh_token = create_token(user_id=user.id, type="refresh")

    access_max_age = settings.jwt.access_token_expire_in_minutes * 60
    res.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        domain=settings.jwt.domain,
        path="/",
        secure=settings.debug is False,
        samesite="lax",
        max_age=access_max_age,
    )

    refresh_max_age = settings.jwt.refresh_token_expire_in_days * 86400
    res.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        domain=settings.jwt.domain,
        path="/",
        secure=settings.debug is False,
        samesite="lax",
        max_age=refresh_max_age,
    )

    await SessionsRepository.create(user_id=user.id, user_agent=user_agent, ip_addr=ip_addr, device_name="", refresh_token=refresh_token, session=session)

    return user
