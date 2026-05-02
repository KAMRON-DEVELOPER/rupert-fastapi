from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, field_validator

from src.apps.shared.schemas import RequestSchema, ResponseSchema


def validate_first_name(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("First name should be long between 8 and 24")
    return v


def validate_last_name(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("Last name should be long between 8 and 24")
    return v


def validate_password(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("Password should be long between 8 and 24")
    return v


class PasswordSetupRequest(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 8 or len(v) > 24:
            raise ValueError("Password should be long between 8 and 24")
        return v


class EmailAuthRequest(RequestSchema):
    email: EmailStr
    password: Annotated[str, AfterValidator(validate_password)]
    first_name: Annotated[str | None, AfterValidator(validate_first_name)] = None
    last_name: Annotated[str | None, AfterValidator(validate_last_name)] = None


class AuthProbeResponse(ResponseSchema):
    is_authenticated: bool
