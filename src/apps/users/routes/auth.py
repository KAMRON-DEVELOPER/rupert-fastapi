import asyncio
from typing import Annotated
from fastapi import Cookie, HTTPException, Header, Query, Response, status
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from pydantic import BaseModel
from bcrypt import checkpw, gensalt, hashpw
from apps.shared.schemas import MessageRes
from apps.users.repositories.oauth_user import OAuthUsersRepository
from apps.users.repositories.session import SessionsRepository
from apps.users.repositories.user import UsersRepository
from apps.users.utils import finalize_session
from services.mailtrap import Mailtrap, MailtrapError
from src.apps.users.schemas import AuthProbeResponse, EmailAuthSchema, UserUpdateSchema
from src.dependencies.proactive_refresh import authDep, create_token, strictAuthDep
from src.apps.users.routes import users_router

from src.utils.settings import get_settings
from src.utils.oauth import build_pkce_pair, exchange_github_code, exchange_google_code, github_auth_url, google_auth_url
from utils.database import DBSession
from utils.exceptions import ValidationException

settings = get_settings()


@users_router.get("/auth/probe", response_model=AuthProbeResponse)
async def auth_probe(auth: authDep):
    """"""
    return AuthProbeResponse(is_authenticated=auth is not None)


@users_router.get("/auth/google")
async def google_oauth():
    verifier, challenge = build_pkce_pair()
    url = google_auth_url(challenge)
    res = RedirectResponse(url)
    res.set_cookie("pkce_verifier", verifier, httponly=True, samesite="lax", secure=True)
    return res


@users_router.get("/auth/google/callback")
async def google_oauth_callback(req: Request, code: str = Query()):
    verifier = req.cookies.get("pkce_verifier")
    if not verifier:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing PKCE verifier")
    user_info = await exchange_google_code(code, verifier)
    return user_info


@users_router.get("/auth/github")
async def github_oauth():
    verifier, challenge = build_pkce_pair()
    url = github_auth_url(challenge)
    res = RedirectResponse(url)
    res.set_cookie("pkce_verifier", verifier, httponly=True, samesite="lax", secure=True)
    return res


@users_router.get("/auth/github/callback")
async def github_oauth_callback(req: Request, code: str = Query()):
    verifier = req.cookies.get("pkce_verifier")
    if not verifier:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing PKCE verifier")
    user_info = await exchange_github_code(code, verifier)
    return user_info


@users_router.get("/auth/password-setup")
async def password_setup(req: Request):
    pass


@users_router.get(path="/auth/email")
async def email_auth(req: Request, res: Response, schema: EmailAuthSchema, session: DBSession):
    """
    user exist:
        yes: authenticated with oauth:
                yes: [send set-password link, return message response]
                no: match password:
                    yes: [finalize_session, return user]
                    no: return validation error
        no: first_name or schm.last_name provided:
            yes: a
            no: return message response
    """

    user = await UsersRepository.find_by_email(schema.email, session)

    if user:
        if not user.password_hash:
            providers = await OAuthUsersRepository.find_providers_by_user_id(user.id, session)

            if len(providers) == 0:
                print(f"user has no password and no linked oauth provider, {user.id}")
                return HTTPException(status_code=500, detail="This account is missing a login method. Please contact support.")

            token = create_token(user.id, "password_setup")
            setup_link = f"{settings.frontend_endpoint}/auth/set-password?token={token}"

            try:
                await Mailtrap.send_password_setup_link(to_name=f"{user.first_name} {user.last_name}", to_email=user.email, link=setup_link, cfg=settings.mailtrap)
            except MailtrapError as e:
                print(e.error.errors)
                return HTTPException(status_code=500, detail="Could not send password setup link")

            providers_text = ", ".join(str(p.value) for p in providers)
            return MessageRes(msg=f"This account was created with {providers_text}. Use that provider to sign in, or use the link we sent to set a password.")

        is_valid = await asyncio.to_thread(checkpw, schema.password.encode(), user.password_hash.encode())
        if not is_valid:
            raise ValidationException("password is not match.")

        user = await finalize_session(user, req, res, session)
        await session.commit()
        return user

    if not schema.first_name or not schema.last_name:
        return MessageRes(msg="new_user")

    hash_password_bytes = await asyncio.to_thread(hashpw, schema.password.encode(), gensalt(rounds=8))
    hash_password = hash_password_bytes.decode()
    user = await UsersRepository.create(schema.email, hash_password, schema.first_name, schema.last_name, session)

    token = create_token(user.id, "email_verification")
    verification_link = f"{settings.frontend_endpoint}/auth/verify?token={token}"

    try:
        await Mailtrap.send_email_verification_link(to_name=f"{schema.first_name} {schema.last_name}", to_email=schema.email, link=verification_link, cfg=settings.mailtrap)
    except MailtrapError as e:
        print(e.error.errors)
        return HTTPException(status_code=500, detail="Could not send email verification link")

    user = await finalize_session(user, req, res, session)
    await session.commit()
    return user


@users_router.get("/auth/logout")
async def logout(auth: strictAuthDep, session: DBSession):
    return await SessionsRepository.delete(auth, session)


@users_router.get("/")
async def get_user(auth: strictAuthDep, session: DBSession):
    return await UsersRepository.get_by_id(auth, session)


@users_router.get("/")
async def update_user(auth: strictAuthDep, schema: UserUpdateSchema, session: DBSession):
    return await UsersRepository.update_by_id(auth, schema, session)


@users_router.get("/")
async def delete_user(auth: strictAuthDep, session: DBSession):
    pass


# ***********************************************


class Cookies(BaseModel):
    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None

    model_config = {"extra": "forbid"}


@users_router.get("/items/")
async def read_items(cookies: Annotated[Cookies, Cookie()]):
    return cookies


class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

    model_config = {"extra": "forbid"}


@users_router.get("/items/")
async def read_items2(headers: Annotated[CommonHeaders, Header()]):
    return headers


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.perf_counter()
#     response = await call_next(request)
#     process_time = time.perf_counter() - start_time
#     response.headers["X-Process-Time"] = str(process_time)
#     return response


@users_router.get("/login")
def login(response: Response):
    # Set the cookie with the httponly flag
    response.set_cookie(
        key="session_id",
        value="secure_session_token",
        httponly=True,  # Prevents JavaScript access
        secure=True,  # Recommended: Only send over HTTPS
        samesite="lax",  # Recommended: CSRF protection
    )
    return {"message": "Cookie set successfully"}
