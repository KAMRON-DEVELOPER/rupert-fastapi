import asyncio
from pprint import pprint
from typing import Annotated

from bcrypt import gensalt, hashpw
from dead_simple_oauth_fastapi import GithubUser, GoogleUser
from fastapi import Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import update
from starlette.requests import Request

from src.apps.shared.enums import UserStatus
from src.apps.users.models import UserModel
from src.apps.users.schemas import AuthProbeOut, PasswordSetupIn
from src.apps.users.utils import finalize_session
from src.core.database import DBSession
from src.core.logger import logger
from src.core.oauth import github, google
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import decode_token

from .router import users_router

settings = get_settings()


@users_router.get("/auth/google")
async def google_oauth(req: Request):
    return await google.redirect(req)


@users_router.get("/auth/google/callback")
async def google_oauth_callback(
    req: Request,
    res: Response,
    oauth_user: Annotated[GoogleUser, Depends(google.callback_dependency())],
    session: DBSession,
):
    try:
        user = UserModel(
            email=oauth_user.email,
            email_verified=oauth_user.email_verified,
            first_name=oauth_user.given_name,
            last_name=oauth_user.family_name,
            status=UserStatus.active,
        )
        session.add(user)
        await session.flush()

        await finalize_session(req, res, user, session)
        return RedirectResponse(settings.frontend_endpoint)
    except Exception as e:
        logger.error("google_oauth_callback [session.flush, finalize_session]")
        pprint(e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@users_router.get("/auth/github")
async def github_oauth(request: Request):
    return await github.redirect(request)


@users_router.get("/auth/github/callback")
async def github_oauth_callback(
    req: Request,
    res: Response,
    oauth_user: Annotated[GithubUser, Depends(github.callback_dependency())],
    session: DBSession,
):
    try:
        user = UserModel(
            email=oauth_user.email,
            email_verified=True,
            first_name=oauth_user.name,
            last_name=None,
            status=UserStatus.active,
        )
        session.add(user)
        await session.flush()

        await finalize_session(req, res, user, session)
        return RedirectResponse(settings.frontend_endpoint)
    except Exception as e:
        logger.error("google_oauth_callback [session.flush, finalize_session]")
        pprint(e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@users_router.post("/auth/password-setup")
async def password_setup(token: Annotated[str, Query], schm: PasswordSetupIn, session: DBSession):
    decoded = decode_token(token, "password_setup")

    hash_password_bytes = await asyncio.to_thread(hashpw, schm.password.encode(), gensalt(rounds=8))
    hash_password = hash_password_bytes.decode()

    stmt = update(UserModel).where(UserModel.id == decoded.sub).values(hash_password=hash_password)
    try:
        await session.execute(stmt)
    except Exception as e:
        logger.error("password_setup session.execute")
        pprint(e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
