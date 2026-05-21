from uuid import UUID

from pydantic import Field

from .base import BaseModelResponse, RequestSchema


class LocationRequest(RequestSchema):
    country_id: UUID
    city_id: UUID | None = None


class NullableLocationRequest(RequestSchema):
    country_id: UUID | None = None
    city_id: UUID | None = None


class BaseLocationModelResponse(BaseModelResponse):
    country: CountryResponse
    city: CityResponse | None


class BaseNullableLocationModelResponse(BaseModelResponse):
    country: CountryResponse | None
    city: CityResponse | None


class CountryCreateRequest(RequestSchema):
    code: str = Field(max_length=2)
    name: str = Field(max_length=56)


class CountryUpdateRequest(RequestSchema):
    code: str | None = Field(default=None, max_length=2)
    name: str | None = Field(default=None, max_length=56)


class CountryResponse(BaseModelResponse):
    code: str
    name: str


class CityRequest(RequestSchema):
    name: str = Field(max_length=168)


class CityResponse(BaseModelResponse):
    country_id: UUID
    name: str
