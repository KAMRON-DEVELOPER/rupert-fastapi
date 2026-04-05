from typing import Annotated, Optional

from fastapi import Depends, Query


class PaginationQueryParams:

    def __init__(self, offset: Optional[int] = Query(default=0), limit: Optional[int] = Query(default=100)):
        self.offset = offset
        self.limit = limit


paginationDep = Annotated[PaginationQueryParams, Depends()]
