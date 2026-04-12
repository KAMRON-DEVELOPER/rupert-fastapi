from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, model_validator
from pydantic.fields import Field


class Pagination(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=0)

    @model_validator(mode="after")
    def check_offset_less_than_limit(self) -> Pagination:
        if self.offset > self.limit:
            raise ValueError("Offset cannot be greater than limit")
        return self

    model_config = {"extra": "forbid"}


paginationDep = Annotated[Pagination, Query()]
