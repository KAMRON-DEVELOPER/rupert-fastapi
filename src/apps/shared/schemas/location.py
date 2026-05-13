from pydantic import Field

from .base import BaseModelResponse, RequestSchema


class LocationRequest(RequestSchema):
    country: str = Field(max_length=64)
    city: str = Field(max_length=64)


class NullableLocationRequest(RequestSchema):
    country: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=64)


class BaseLocationModelResponse(BaseModelResponse):
    country: str
    city: str


class BaseNullableLocationModelResponse(BaseModelResponse):
    country: str | None
    city: str | None
