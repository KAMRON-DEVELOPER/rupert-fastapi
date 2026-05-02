from pydantic import Field

from .base import RequestSchema, ResponseSchema


class TagRequest(RequestSchema):
    name: str = Field(max_length=64)


class TagResponse(ResponseSchema):
    name: str
