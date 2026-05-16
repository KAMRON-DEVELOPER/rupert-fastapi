import asyncio
from pprint import pprint
from typing import Annotated

from bcrypt import gensalt, hashpw
from fastapi import HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import update

from src.apps.shared.schemas.enums import UserStatus
from src.apps.users.models import UserModel
from src.apps.users.schemas.auth import PasswordSetupRequest
from src.apps.users.utils import finalize_session
from src.core.database import sessionDep
from src.core.logger import logger
from src.core.oauth import GithubUserDep, GoogleUserDep, github, google
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import decode_token

from .router import users_router

settings = get_settings()


@users_router.get("/auth/google")
async def google_oauth(req: Request):
    return await google.redirect(req)


@users_router.get("/auth/google/callback")
async def google_oauth_callback(
    req: Request, oauth_user: GoogleUserDep, session: sessionDep
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

        redirect = RedirectResponse(settings.frontend_endpoint)
        await finalize_session(req, redirect, user.id, session)
        return redirect
    except Exception as e:
        logger.error("google_oauth_callback [session.flush, finalize_session]")
        pprint(e)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong"
        )


@users_router.get("/auth/github")
async def github_oauth(request: Request):
    return await github.redirect(request)


@users_router.get("/auth/github/callback")
async def github_oauth_callback(
    req: Request, oauth_user: GithubUserDep, session: sessionDep
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

        redirect = RedirectResponse(settings.frontend_endpoint)
        await finalize_session(req, redirect, user.id, session)
        return redirect
    except Exception as e:
        logger.error("google_oauth_callback [session.flush, finalize_session]")
        pprint(e)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong"
        )


@users_router.post("/auth/password-setup")
async def password_setup(
    token: Annotated[str, Query],
    schm: PasswordSetupRequest,
    session: sessionDep,
):
    decoded = decode_token(token, "password_setup")

    password_hash_bytes = await asyncio.to_thread(
        hashpw, schm.password.encode(), gensalt(rounds=8)
    )
    password_hash = password_hash_bytes.decode()

    stmt = (
        update(UserModel)
        .where(UserModel.id == decoded.sub)
        .values(password_hash=password_hash)
    )
    try:
        await session.execute(stmt)
    except Exception as e:
        logger.error("password_setup session.execute")
        pprint(e)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong"
        )
