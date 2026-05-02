from pprint import pprint

from fastapi import HTTPException, status

from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.companies.schemas.company import CompanySummary, companyListDep
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.core.database import DBSession
from src.core.logger import logger

from .router import companies_router


@companies_router.get("/", response_model=PaginatedResponse[CompanySummary])
async def list_companies(pagination: paginationDep, filters: companyListDep, session: DBSession):
    try:
        return await CompaniesRepository.get_many(session=session, pagination=pagination, filters=filters)
    except Exception as e:
        logger.error("list_companies CompaniesRepository.get_many")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
