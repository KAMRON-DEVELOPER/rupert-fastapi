import asyncio
from typing import Annotated

from bcrypt import checkpw, gensalt, hashpw
from dead_simple_oauth_fastapi import GithubUser, GoogleUser
from fastapi import Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import update
from starlette.requests import Request

from src.apps.shared.enums import UserStatus
from src.apps.shared.schemas import MessageResponse
from src.apps.users.models import UserModel
from src.apps.users.repositories.oauth_user import OAuthUsersRepository
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas import AuthProbeOut, EmailAuthIn, PasswordSetupIn, UserUpdateIn
from src.apps.users.utils import finalize_session
from src.core.database import DBSession
from src.core.exceptions import ValidationException
from src.core.logger import logger
from src.core.oauth import github, google
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import authDep, authProbeDep, create_token, decode_token
from src.services.mailtrap import Mailtrap, MailtrapError

from .router import users_router

settings = get_settings()


@users_router.get("/auth/probe", response_model=AuthProbeOut)
async def auth_probe(auth: authProbeDep):
    """Helpfull handler to check user session validity"""
    return AuthProbeOut(is_authenticated=auth is not None)


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
        logger.error("google_oauth_callback", e)
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
        logger.error("google_oauth_callback", e)
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
        logger.error("password_setup", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@users_router.post(path="/auth/email", status_code=status.HTTP_201_CREATED)
async def email_auth(req: Request, res: Response, schm: EmailAuthIn, session: DBSession):
    try:
        user = await UsersRepository.find_by_email(schm.email, session)
    except Exception as e:
        logger.error("email_auth UsersRepository.find_by_email", e)
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
                logger.error("email_auth finalize_session", e)
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
            return user

        try:
            providers = await OAuthUsersRepository.find_providers_by_user_id(user.id, session)
        except Exception as e:
            logger.error("email_auth OAuthUsersRepository.find_providers_by_user_id", e)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

        if len(providers) == 0:
            print(f"user has no password and no linked oauth provider, {user.id}")
            raise HTTPException(status_code=500, detail="This account is missing a login method. Please contact support.")

        token = create_token(user.id, "password_setup")
        setup_link = f"{settings.frontend_endpoint}/auth/set-password?token={token}"

        try:
            await Mailtrap.send_password_setup_link(to_name=f"{user.first_name} {user.last_name}", to_email=user.email, link=setup_link, cfg=settings.mailtrap)
        except MailtrapError as e:
            logger.error("MailtrapError", e.error.errors)
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
        logger.error("email_auth UsersRepository.create", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

    token = create_token(user.id, "email_verification")
    verification_link = f"{settings.frontend_endpoint}/auth/verify?token={token}"

    try:
        await Mailtrap.send_email_verification_link(to_name=f"{schm.first_name} {schm.last_name}", to_email=schm.email, link=verification_link, cfg=settings.mailtrap)
    except MailtrapError as e:
        logger.error("MailtrapError", e.error.errors)
        raise HTTPException(status_code=500, detail="Could not send email verification link")

    try:
        await finalize_session(req, res, user, session)
        await session.commit()
    except Exception as e:
        logger.error("email_auth finalize_session", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
    return user


@users_router.post("/auth/logout")
async def logout(auth: authDep, session: DBSession):
    user_id, _, refresh_token = auth

    try:
        return await SessionsRepository.delete(user_id, refresh_token, session)
    except Exception as e:
        logger.error("logout", e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@users_router.get("/")
async def get_user(auth: authDep, session: DBSession):
    user_id, _, _ = auth

    try:
        return await UsersRepository.get_by_id(user_id, session)
    except Exception as e:
        logger.error("get_user", e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@users_router.patch("/")
async def update_user(auth: authDep, schm: UserUpdateIn, session: DBSession):
    user_id, _, _ = auth

    try:
        return await UsersRepository.update_by_id(user_id, schm, session)
    except Exception as e:
        logger.error("update_user", e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@users_router.delete("/")
async def delete_user(auth: authDep, session: DBSession):
    user_id, _, refresh_token = auth

    try:
        await SessionsRepository.delete(user_id, refresh_token, session)
        await UsersRepository.delete_by_id(user_id, session)
    except Exception as e:
        logger.error("update_user", e)
        raise HTTPException(status_code=500, detail="Something went wrong")
