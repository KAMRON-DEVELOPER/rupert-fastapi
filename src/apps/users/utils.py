from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.proactive_refresh import create_token, set_auth_cookie
from src.apps.models import UserModel
from src.apps.users.repositories.session import SessionsRepository
from src.utils.settings import get_settings

settings = get_settings()


async def finalize_session(req: Request, res: Response, user: UserModel, session: AsyncSession):
    user_agent = req.headers.get("user-agent", "unknown")
    ip_addr = req.client.host if req.client else "unknown"

    new_access_token = create_token(user_id=user.id, type="access")
    new_refresh_token = create_token(user_id=user.id, type="refresh")

    set_auth_cookie(res, key="access_token", value=new_access_token, max_age=settings.jwt.access_token_expire_in_minutes * 60)
    set_auth_cookie(res, key="refresh_token", value=new_refresh_token, max_age=settings.jwt.refresh_token_expire_in_days * 86400)

    await SessionsRepository.create(
        user_id=user.id,
        user_agent=user_agent,
        ip_addr=ip_addr,
        device_name="",
        refresh_token=new_refresh_token,
        session=session,
    )
