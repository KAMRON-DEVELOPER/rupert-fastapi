from typing import Annotated, Generic, TypeVar

from fastapi import Depends
from pydantic import Field

from .base import RequestSchema, ResponseSchema


class PaginationQuery(RequestSchema):
    offset: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


paginationDep = Annotated[PaginationQuery, Depends()]

T = TypeVar("T")


class PaginatedResponse(ResponseSchema, Generic[T]):
    data: list[T]
    total: int
