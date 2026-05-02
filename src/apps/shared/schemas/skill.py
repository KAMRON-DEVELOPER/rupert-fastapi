from pydantic import Field

from .base import RequestSchema, ResponseSchema


class SkillRequest(RequestSchema):
    name: str = Field(max_length=64)


class SkillResponse(ResponseSchema):
    name: str
