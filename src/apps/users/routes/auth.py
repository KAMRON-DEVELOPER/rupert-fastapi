import asyncio
from typing import Annotated
from urllib.parse import urljoin

from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from src.apps.shared.schemas import MessageResponse
from src.apps.users.repositories.oauth_user import OAuthUsersRepository
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas.auth import (
    AuthProbeResponse,
    EmailAuthRequest,
    EmailAuthResponse,
)
from src.apps.users.utils import finalize_session
from src.core.database import sessionDep
from src.core.exceptions import ValidationException
from src.core.logger import logger
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import (
    authDep,
    authProbeDep,
    clear_auth_cookies,
    create_token,
    decode_token,
)
from src.services.mailtrap import Mailtrap

from .router import users_router

settings = get_settings()


@users_router.get("/auth/probe", response_model=AuthProbeResponse)
async def auth_probe(auth: authProbeDep):
    """Helpful handler to check user session validity"""
    return AuthProbeResponse(is_authenticated=auth is not None)


@users_router.post(path="/auth/email")
async def email_auth(
    req: Request, res: Response, schm: EmailAuthRequest, session: sessionDep
):
    user = await UsersRepository.get_by_email(session, schm.email, False)

    if user:
        if user.password_hash:
            is_valid = await asyncio.to_thread(
                checkpw, schm.password.encode(), user.password_hash.encode()
            )
            if not is_valid:
                raise ValidationException("password is not match.")

            await finalize_session(req, res, session, user.id)
            await session.commit()
            return EmailAuthResponse.model_validate(user)

        # Password not set
        providers = await OAuthUsersRepository.find_providers_by_user_id(
            session, user.id
        )

        if len(providers) == 0:
            logger.critical(
                f"user has no password and no linked oauth provider, {user.id}"
            )
            raise HTTPException(
                status_code=500,
                detail="This account is missing a login method. Please contact support.",
            )

        token = create_token(user.id, "password_setup")
        link = f"{settings.frontend_endpoint}/auth/set-password?token={token}"

        await Mailtrap.send_password_setup_link(
            f"{user.first_name} {user.last_name}",
            user.email,
            link,
            settings.mailtrap,
        )

        providers_text = ", ".join(str(p.value) for p in providers)
        return MessageResponse(
            message=f"This account was created with {providers_text}. Use that provider to sign in, or use the link we sent to set a password."
        )

    if not schm.first_name or not schm.last_name:
        return MessageResponse(message="new_user")

    hash_password_bytes = await asyncio.to_thread(
        hashpw, schm.password.encode(), gensalt(rounds=8)
    )
    hash_password = hash_password_bytes.decode()

    user = await UsersRepository.create(
        session, schm.email, schm.first_name, schm.last_name, hash_password
    )

    await finalize_session(req, res, session, user.id)

    token = create_token(user.id, "email_verification")
    link = f"{settings.frontend_endpoint}/auth/verify?token={token}"

    try:
        await Mailtrap.send_email_verification_link(
            f"{schm.first_name} {schm.last_name}",
            schm.email,
            link,
            settings.mailtrap,
        )

        await session.commit()
    except HTTPException as e:
        await session.rollback()
        clear_auth_cookies(res)
        raise e

    return EmailAuthResponse.model_validate(user)


@users_router.post("/auth/verify")
async def verify(
    token: Annotated[str, Query()], auth: authProbeDep, session: sessionDep
):
    claims = decode_token(token, "email_verification")

    if auth:
        if auth[0] != claims.sub:
            content = MessageResponse(
                message="You are not the same person!"
            ).model_dump_json()
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST, content=content
            )

    await UsersRepository.set_email_verified(session, claims.sub)
    await session.commit()

    if auth:
        return MessageResponse(message="Your email verified successfully")
    else:
        base = settings.frontend_endpoint.rstrip("/")
        url = urljoin(base, "auth")
        return RedirectResponse(url)


@users_router.post("/auth/logout")
async def logout(res: Response, auth: authDep, session: sessionDep):
    user_id, _, refresh_token = auth

    await SessionsRepository.delete(session, user_id, refresh_token)
    await session.commit()

    clear_auth_cookies(res)

    return MessageResponse(message="You successfully logged out")
