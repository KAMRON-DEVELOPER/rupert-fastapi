from pprint import pprint
from typing import Annotated

from fastapi import Depends, HTTPException, status

from src.apps.shared.schemas import Pagination
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.apps.vacancies.schemas import ApplicationFilters, ApplicationOut, VacancyCardOut, VacancyFilters
from src.core.database import DBSession
from src.core.logger import logger
from src.dependencies.proactive_refresh import authProbeDep

from .router import vacancies_router


@vacancies_router.get("/", response_model=list[VacancyCardOut])
async def list_vacancies(pagination: Annotated[Pagination, Depends()], filters: Annotated[VacancyFilters, Depends()], auth: authProbeDep, session: DBSession):
    user_id = auth[0] if auth else None
    try:
        return await VacanciesRepository.get_many(session=session, user_id=user_id, pagination=pagination, filters=filters)
    except Exception as e:
        logger.error("list_vacancies VacanciesRepository.get_many")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@vacancies_router.get("/applications", response_model=list[ApplicationOut])
async def list_applications(pagination: Annotated[Pagination, Depends()], filters: Annotated[ApplicationFilters, Depends()], session: DBSession):
    try:
        return await VacanciesRepository.get_applications(session=session, pagination=pagination, filters=filters)
    except Exception as e:
        logger.error("list_applications VacanciesRepository.get_applications")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
