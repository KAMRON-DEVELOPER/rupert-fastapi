from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.responses import Response
from jwt import decode, encode
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from pydantic import BaseModel, ValidationError

from src.utils.settings import get_settings

settings = get_settings()


CookieTokenType = Literal["access", "refresh"]
TokenType = Literal[*CookieTokenType, "email_verification", "password_setup"]


class TokenClaims(BaseModel):
    sub: UUID
    type: TokenType
    exp: datetime
    iat: datetime


class AuthCookies(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None

    model_config = {"extra": "forbid"}


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

    return encode(payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)


def decode_token(jwt: str, expected_type: TokenType):
    try:
        # We emit new access token if expired, no raise
        verify_exp = expected_type != "access"
        obj = decode(
            jwt,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
            options={"verify_exp": verify_exp},
        )

        claims = TokenClaims.model_validate(obj)

        if claims.type != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        return claims
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT token validation error")
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
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT error")


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


def set_auth_cookie(res: Response, key: str, value: str, max_age: int):
    res.set_cookie(key=key, value=value, max_age=max_age, domain=settings.jwt.domain, path="/", secure=not settings.debug, httponly=True, samesite="lax")


def clear_auth_cookies(res: Response):
    res.delete_cookie(key="access_token", domain=settings.jwt.domain, path="/")
    res.delete_cookie(key="refresh_token", domain=settings.jwt.domain, path="/")


class ProactiveRefresh:
    def __init__(self, required: bool = False):
        self.required = required

    def __call__(self, res: Response, auth_cookies: Annotated[AuthCookies, Cookie()]):
        access_token = auth_cookies.access_token
        refresh_token = auth_cookies.refresh_token

        if access_token:
            access_needs_refresh, access_claims, expired = handle_decode(access_token, "access")
            if not expired:
                if access_needs_refresh:
                    new_access_token = create_token(user_id=access_claims.sub, type="access")
                    set_auth_cookie(res, key="access_token", value=new_access_token, max_age=settings.jwt.access_token_expire_in_minutes * 60)
                return access_claims.sub, access_token, refresh_token

        if refresh_token:
            refresh_needs_refresh, refresh_claims, _ = handle_decode(refresh_token, "refresh")

            new_access_token = create_token(user_id=refresh_claims.sub, type="access")
            set_auth_cookie(res, key="access_token", value=new_access_token, max_age=settings.jwt.access_token_expire_in_minutes * 60)

            if refresh_needs_refresh:
                new_refresh_token = create_token(user_id=refresh_claims.sub, type="refresh")
                set_auth_cookie(res, key="refresh_token", value=new_refresh_token, max_age=settings.jwt.refresh_token_expire_in_days * 86400)

            return refresh_claims.sub, access_token, refresh_token

        if self.required:
            raise HTTPException(status_code=401, detail="Not authenticated")

        return None


auth_probe_checker = ProactiveRefresh()
authProbeDep = Annotated[tuple[UUID, str, str] | None, Depends(auth_probe_checker)]

auth_checker = ProactiveRefresh(required=True)
authDep = Annotated[tuple[UUID, str, str], Depends(auth_checker)]
