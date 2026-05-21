import asyncio
from typing import Annotated, cast
from urllib.parse import urljoin

from bcrypt import gensalt, hashpw
from faker import Faker
from fastapi import HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from src.apps.shared.schemas.enums import Provider
from src.apps.users.models import UserModel
from src.apps.users.repositories.oauth_user import OAuthUsersRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas.auth import PasswordSetupRequest
from src.apps.users.utils import finalize_session
from src.core.database import sessionDep
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
    req: Request, google_user: GoogleUserDep, session: sessionDep
):
    oauth_user = await OAuthUsersRepository.get_by_provider_id(
        session, google_user.sub, False
    )

    if oauth_user:
        user = await UsersRepository.get_summary(
            session,
            oauth_user.user_id,
        )
        user = cast(UserModel, user)
    else:
        if not google_user.email:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email is not optional, we do not support that yet, reach contact support",
            )

        fake = Faker()
        first_name = google_user.given_name or fake.first_name()
        last_name = google_user.family_name or fake.last_name()

        user = await UsersRepository.create(
            session,
            google_user.email,
            first_name,
            last_name,
            email_verified=True,
        )
        await OAuthUsersRepository.create(
            session, google_user.sub, user.id, Provider.google, google_user.name
        )

    redirect = RedirectResponse(settings.frontend_endpoint)
    await finalize_session(req, redirect, session, user.id)
    await session.commit()
    return redirect


@users_router.get("/auth/github")
async def github_oauth(request: Request):
    return await github.redirect(request)


@users_router.get("/auth/github/callback")
async def github_oauth_callback(
    req: Request, github_user: GithubUserDep, session: sessionDep
):
    oauth_user = await OAuthUsersRepository.get_by_provider_id(
        session, str(github_user.id), False
    )

    if oauth_user:
        user = await UsersRepository.get_summary(
            session,
            oauth_user.user_id,
        )
        user = cast(UserModel, user)
    else:
        if not github_user.email:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email is not optional, we do not support that yet, reach contact support",
            )

        fake = Faker()
        parts = (github_user.name or "").split(" ", maxsplit=1)
        first_name = (parts[0] if len(parts) > 0 else None) or fake.first_name()
        last_name = (parts[1] if len(parts) > 1 else None) or fake.last_name()

        user = await UsersRepository.create(
            session,
            github_user.email,
            first_name,
            last_name,
            email_verified=True,
        )
        await OAuthUsersRepository.create(
            session,
            str(github_user.id),
            user.id,
            Provider.google,
            github_user.login,
        )

    redirect = RedirectResponse(settings.frontend_endpoint)
    await finalize_session(req, redirect, session, user.id)
    await session.commit()
    return redirect


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

    await UsersRepository.update(
        session, decoded.sub, {"password_hash": password_hash}
    )
    await session.commit()

    base = settings.frontend_endpoint.rstrip("/")
    url = urljoin(base, "auth")
    return RedirectResponse(url)
