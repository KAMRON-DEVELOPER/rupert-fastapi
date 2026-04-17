from datetime import datetime
from typing import Annotated, Generic, TypeVar
from uuid import UUID

from pydantic import AfterValidator, AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class ORMSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CameCaseOut(ORMSchema):
    model_config = ConfigDict(from_attributes=True, alias_generator=AliasGenerator(serialization_alias=to_camel))


class BaseOut(CameCaseOut):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
T = TypeVar("T")


class PaginatedOut(ORMSchema, Generic[T]):
    data: list[T]
    total: int


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------
def validate_country(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("Country should be long between 8 and 24")
    return v


def validate_city(v: str | None) -> str | None:
    if v and (len(v) < 8 or len(v) > 24):
        raise ValueError("Country should be long between 8 and 24")
    return v


class LocationIn(BaseModel):
    country: Annotated[str | None, AfterValidator(validate_country)]
    city: Annotated[str | None, AfterValidator(validate_city)]


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------
class TagIn(BaseModel):
    name: str = Field(max_length=64)


class TagOut(BaseOut):
    name: str


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------
class SkillIn(BaseModel):
    name: str = Field(max_length=64)


class SkillOut(BaseOut):
    name: str


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------
class MessageResponse(BaseModel):
    msg: str = Field(serialization_alias="message")
