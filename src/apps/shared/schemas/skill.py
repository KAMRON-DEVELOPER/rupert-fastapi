from pydantic import Field

from .base import BaseModelResponse, RequestSchema


class SkillRequest(RequestSchema):
    name: str = Field(max_length=64)


class SkillResponse(BaseModelResponse):
    name: str
