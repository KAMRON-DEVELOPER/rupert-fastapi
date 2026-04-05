from datetime import UTC, datetime, timedelta
import re
from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from jwt.exceptions import PyJWTError
from jwt import decode, encode
from jwt.types import Options
from pydantic import BaseModel, ValidationError

from src.utils.settings import get_settings

settings = get_settings()


TokenType = Literal["access", "refresh", "email_verification", "password_setup"]


class TokenClaims(BaseModel):
    sub: UUID
    type: TokenType
    exp: datetime
    iat: datetime


def create_token(user_id: UUID, type: TokenType) -> str:
    iat = datetime.now(UTC)

    minutes = settings.jwt.access_token_expire_in_minutes
    days = settings.jwt.refresh_token_expire_in_days
    exp = iat + (timedelta(minutes=minutes) if type == "access" else timedelta(days=days))

    claims = TokenClaims(sub=user_id, type=type, exp=exp, iat=iat)
    payload = claims.model_dump()

    return encode(payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)


def to_snake_case(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def decode_token(jwt: str) -> tuple[bool, TokenClaims]:
    try:
        obj = decode(jwt, options=Options(verify_signature=False))

        claims = TokenClaims.model_validate(obj)

        minutes = settings.jwt.access_token_renewal_threshold_minutes
        days = settings.jwt.refresh_token_renewal_threshold_days
        threshold = timedelta(minutes=minutes) if claims.type == "access" else timedelta(days=days)

        if claims.exp - datetime.now(UTC) < threshold:
            return (True, claims)

        return (False, claims)
    except Exception as e:
        if isinstance(e, ValidationError):
            print(f"Validation error: {e}")
            raise
        elif isinstance(e, PyJWTError):
            exception_class_name = type(e).__name__
            snake_case_name = to_snake_case(exception_class_name)
            detail = f"JWT {snake_case_name.replace('_error', '').replace('_signature', ' signature')} error"
            print(detail)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
        else:
            raise


security = HTTPBearer()
authHeaderDep = Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
cookieDep = Annotated[Optional[str], Cookie()]


async def proactive_refresh(res: Response, access_token: cookieDep, refresh_token: cookieDep) -> UUID:
    user_id: Optional[UUID] = None

    if access_token:
        needs_refresh, claims = decode_token(access_token)
        user_id = claims.sub
        if needs_refresh:
            new_access_token = create_token(user_id=claims.sub, type=claims.type)
            max_age = settings.jwt.access_token_expire_in_minutes * 60
            res.set_cookie(
                key="access_token", value=new_access_token, httponly=True, domain=settings.jwt.domain, path="/", secure=settings.debug is False, samesite="lax", max_age=max_age
            )

    if refresh_token:
        needs_refresh, claims = decode_token(refresh_token)
        user_id = claims.sub
        if needs_refresh:
            new_refresh_token = create_token(user_id=claims.sub, type=claims.type)
            max_age = settings.jwt.refresh_token_expire_in_days * 86400
            res.set_cookie(
                key="refresh_token", value=new_refresh_token, httponly=True, domain=settings.jwt.domain, path="/", secure=settings.debug is False, samesite="lax", max_age=max_age
            )

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return user_id


class ProactiveRefresh:
    def __init__(self, optional: bool = False):
        self.optional = optional

    def __call__(self, q: str = ""):
        pass


checker = ProactiveRefresh()
authDep = Annotated[Optional[UUID], Depends(checker)]

strictChecker = ProactiveRefresh()
strictAuthDep = Annotated[UUID, Depends(strictChecker)]
