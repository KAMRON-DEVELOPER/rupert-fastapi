from typing import Annotated

from fastapi import Depends, Query


class PaginationQueryParams:

    def __init__(self, offset: int | None = Query(default=0), limit: int | None = Query(default=100)):
        self.offset = offset
        self.limit = limit


paginationDep = Annotated[PaginationQueryParams, Depends()]
