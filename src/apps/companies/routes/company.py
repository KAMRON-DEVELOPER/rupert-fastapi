from pprint import pprint
from typing import Annotated

from fastapi import Depends, HTTPException, status

from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.companies.schemas.company import CompanyCardOut, CompanyFilters
from src.apps.shared.schemas import PaginatedOut, Pagination
from src.core.database import DBSession
from src.core.logger import logger
from src.dependencies.proactive_refresh import authProbeDep

from .router import companies_router


@companies_router.get("/", response_model=PaginatedOut[CompanyCardOut])
async def list_companies(pagination: Annotated[Pagination, Depends()], filters: Annotated[CompanyFilters, Depends()], auth: authProbeDep, session: DBSession):
    try:
        return await CompaniesRepository.get_many(session=session, pagination=pagination, filters=filters)
    except Exception as e:
        logger.error("list_companies CompaniesRepository.get_many")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
