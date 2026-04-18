import asyncio
from pprint import pprint
from typing import Annotated
from urllib.parse import urljoin

from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from src.apps.shared.schemas import MessageResponse
from src.apps.users.repositories.oauth_user import OAuthUsersRepository
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas import AuthProbeOut, EmailAuthIn
from src.apps.users.utils import finalize_session
from src.core.database import DBSession
from src.core.exceptions import ValidationException
from src.core.logger import logger
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import authDep, authProbeDep, create_token, decode_token
from src.services.mailtrap import Mailtrap, MailtrapError

from .router import users_router

settings = get_settings()


@users_router.get("/auth/probe", response_model=AuthProbeOut)
async def auth_probe(auth: authProbeDep):
    """Helpfull handler to check user session validity"""
    return AuthProbeOut(is_authenticated=auth is not None)


@users_router.post(path="/auth/email")
async def email_auth(req: Request, res: Response, schm: EmailAuthIn, session: DBSession):
    try:
        user = await UsersRepository.find_by_email(schm.email, session)
    except Exception as e:
        logger.error("email_auth UsersRepository.find_by_email")
        pprint(e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

    if user:
        if user.password_hash:
            is_valid = await asyncio.to_thread(checkpw, schm.password.encode(), user.password_hash.encode())
            if not is_valid:
                raise ValidationException("password is not match.")

            try:
                await finalize_session(req, res, user, session)
                await session.commit()
            except Exception as e:
                logger.error("email_auth finalize_session")
                pprint(e)
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
            return user

        try:
            providers = await OAuthUsersRepository.find_providers_by_user_id(user.id, session)
        except Exception as e:
            logger.error("email_auth OAuthUsersRepository.find_providers_by_user_id")
            pprint(e)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

        if len(providers) == 0:
            print(f"user has no password and no linked oauth provider, {user.id}")
            raise HTTPException(status_code=500, detail="This account is missing a login method. Please contact support.")

        token = create_token(user.id, "password_setup")
        setup_link = f"{settings.frontend_endpoint}/auth/set-password?token={token}"

        try:
            await Mailtrap.send_password_setup_link(to_name=f"{user.first_name} {user.last_name}", to_email=user.email, link=setup_link, cfg=settings.mailtrap)
        except MailtrapError as e:
            logger.error("email_auth MailtrapError")
            pprint(e)
            raise HTTPException(status_code=500, detail="Could not send password setup link")

        providers_text = ", ".join(str(p.value) for p in providers)
        return MessageResponse(msg=f"This account was created with {providers_text}. Use that provider to sign in, or use the link we sent to set a password.")

    if not schm.first_name or not schm.last_name:
        return MessageResponse(msg="new_user")

    hash_password_bytes = await asyncio.to_thread(hashpw, schm.password.encode(), gensalt(rounds=8))
    hash_password = hash_password_bytes.decode()

    try:
        user = await UsersRepository.create(schm.email, hash_password, schm.first_name, schm.last_name, session)
    except Exception as e:
        logger.error("email_auth UsersRepository.create")
        pprint(e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

    token = create_token(user.id, "email_verification")
    verification_link = f"{settings.frontend_endpoint}/auth/verify?token={token}"

    try:
        await Mailtrap.send_email_verification_link(to_name=f"{schm.first_name} {schm.last_name}", to_email=schm.email, link=verification_link, cfg=settings.mailtrap)
    except MailtrapError as e:
        logger.error("email_auth MailtrapError")
        pprint(e)
        raise HTTPException(status_code=500, detail="Could not send email verification link")

    try:
        await finalize_session(req, res, user, session)
        await session.commit()
    except Exception as e:
        logger.error("email_auth finalize_session")
        pprint(e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
    return user


@users_router.post("/auth/verify")
async def verify(token: Annotated[str, Query()], auth: authProbeDep, session: DBSession):
    claims = decode_token(token, "email_verification")

    if auth:
        if auth[0] != claims.sub:
            content = MessageResponse(msg="You are not the same person!").model_dump_json()
            return Response(status_code=status.HTTP_400_BAD_REQUEST, content=content)

    try:
        await UsersRepository.set_email_verified(claims.sub, session)
    except Exception as e:
        logger.error("logout SessionsRepository.delete")
        pprint(e)
        raise HTTPException(status_code=500, detail="Something went wrong")

    if auth:
        return MessageResponse(msg="Your email verified successfully")
    else:
        base = settings.frontend_endpoint.rstrip("/")
        url = urljoin(base, "auth")
        return RedirectResponse(url)


@users_router.post("/auth/logout")
async def logout(auth: authDep, session: DBSession):
    user_id, _, refresh_token = auth

    try:
        return await SessionsRepository.delete(user_id, refresh_token, session)
    except Exception as e:
        logger.error("logout SessionsRepository.delete")
        pprint(e)
        raise HTTPException(status_code=500, detail="Something went wrong")
