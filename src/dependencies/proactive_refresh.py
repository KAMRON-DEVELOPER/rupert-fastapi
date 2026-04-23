from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.responses import Response
from jwt import decode, encode
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from pydantic import BaseModel, ValidationError, field_serializer
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import ActivityModel
from src.core.database import DBSession
from src.core.logger import logger
from src.core.settings import get_settings

settings = get_settings()


CookieTokenType = Literal["access", "refresh"]
ExtraTokenType = Literal["email_verification", "password_setup"]
TokenType = CookieTokenType | ExtraTokenType


class TokenClaims(BaseModel):
    sub: UUID
    type: TokenType
    exp: datetime
    iat: datetime

    @field_serializer("sub")
    def serialize_sub(self, sub: UUID, _info):
        return sub.hex


def create_token(user_id: UUID, type: TokenType) -> str:
    iat = datetime.now(UTC)

    match type:
        case "access":
            exp = iat + timedelta(minutes=settings.jwt.access_token_expire_in_minutes)
        case "refresh":
            exp = iat + timedelta(days=settings.jwt.refresh_token_expire_in_days)
        case "email_verification":
            exp = iat + timedelta(hours=settings.jwt.email_verification_token_expire_in_hours)
        case "password_setup":
            exp = iat + timedelta(minutes=settings.jwt.password_setup_token_expire_in_minutes)

    claims = TokenClaims(sub=user_id, type=type, iat=iat, exp=exp)
    payload = claims.model_dump()
    try:
        return encode(payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
    except Exception as e:
        logger.error(f"Failed to encode token: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to encode token")


def decode_token(jwt: str, expected_type: TokenType):
    # We emit new access token if expired, no raise
    verify_exp = expected_type != "access"

    try:
        obj = decode(jwt, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm], options={"verify_exp": verify_exp})
    except ExpiredSignatureError:
        match expected_type:
            case "access":
                detail = "Access token expired"
            case "refresh":
                detail = "Session expired"
            case "email_verification":
                detail = "Email verification link expired"
            case "password_setup":
                detail = "Password setup link expired"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
    except PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"JWT error: {e}")

    try:
        claims = TokenClaims.model_validate(obj)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation error")

    if claims.type != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    return claims


def handle_decode(jwt: str, expected_type: CookieTokenType) -> tuple[bool, TokenClaims, bool]:
    claims = decode_token(jwt, expected_type=expected_type)

    if expected_type == "access":
        threshold = timedelta(minutes=settings.jwt.access_token_renewal_threshold_minutes)
    else:
        threshold = timedelta(days=settings.jwt.refresh_token_renewal_threshold_days)

    now = datetime.now(UTC)
    exp = claims.exp
    needs_refresh = (exp - now) < threshold
    expired = exp < now

    return (needs_refresh, claims, expired)


def set_cookie(res: Response, key: str, value: str, max_age: int):
    res.set_cookie(key=key, value=value, max_age=max_age, domain=settings.jwt.domain, path="/", secure=not settings.debug, httponly=True, samesite="lax")


def clear_auth_cookies(res: Response):
    res.delete_cookie(key="access_token", domain=settings.jwt.domain, path="/")
    res.delete_cookie(key="refresh_token", domain=settings.jwt.domain, path="/")


class Cookies(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    dau: str | None = None

    model_config = {"extra": "ignore"}


async def upsert_daily_activity(user_id: UUID, activity_date: date, last_activity_at: datetime, session: AsyncSession):
    stmt = insert(ActivityModel).values(user_id=user_id, activity_date=activity_date, last_activity_at=last_activity_at)
    stmt = stmt.on_conflict_do_update(constraint="uq_user_activity_date", set_={"last_activity_at": last_activity_at})
    await session.execute(stmt)


class ProactiveRefresh:
    def __init__(self, required: bool = False):
        self.required = required

    async def __call__(self, res: Response, auth_cookies: Annotated[Cookies, Cookie()], session: DBSession):
        access_token = auth_cookies.access_token
        refresh_token = auth_cookies.refresh_token
        dau = auth_cookies.dau
        user_id = None

        if access_token:
            access_needs_refresh, access_claims, expired = handle_decode(access_token, "access")

            if not expired:
                if access_needs_refresh:
                    new_access_token = create_token(user_id=access_claims.sub, type="access")
                    access_token = new_access_token
                    set_cookie(res, key="access_token", value=new_access_token, max_age=settings.jwt.access_token_expire_in_minutes * 60)

                user_id = access_claims.sub

        if refresh_token:
            refresh_needs_refresh, refresh_claims, _ = handle_decode(refresh_token, "refresh")

            new_access_token = create_token(user_id=refresh_claims.sub, type="access")
            access_token = new_access_token
            set_cookie(res, key="access_token", value=new_access_token, max_age=settings.jwt.access_token_expire_in_minutes * 60)

            if refresh_needs_refresh:
                new_refresh_token = create_token(user_id=refresh_claims.sub, type="refresh")
                refresh_token = new_refresh_token
                set_cookie(res, key="refresh_token", value=new_refresh_token, max_age=settings.jwt.refresh_token_expire_in_days * 86400)

            user_id = refresh_claims.sub

        if not user_id:
            if self.required:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return None

        now = datetime.now(UTC)
        today = now.date()
        today_str = today.isoformat()

        if dau != today_str:
            await upsert_daily_activity(user_id, today, now, session)
            set_cookie(res, key="dau", value=today_str, max_age=86400)

        return user_id, access_token, refresh_token


auth_probe_checker = ProactiveRefresh()
authProbeDep = Annotated[tuple[UUID, str, str] | None, Depends(auth_probe_checker)]

auth_checker = ProactiveRefresh(required=True)
authDep = Annotated[tuple[UUID, str, str], Depends(auth_checker)]
