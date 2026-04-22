from pprint import pprint
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status

from src.apps.shared.schemas import PaginatedOut, Pagination
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.apps.vacancies.schemas.application import ApplicationFilters, ApplicationOut
from src.apps.vacancies.schemas.vacancy import VacancyCardOut, VacancyFilters
from src.core.database import DBSession
from src.core.logger import logger
from src.dependencies.proactive_refresh import authProbeDep

from .router import vacancies_router


@vacancies_router.get("/", response_model=PaginatedOut[VacancyCardOut])
async def list_vacancies(pagination: Annotated[Pagination, Depends()], filters: Annotated[VacancyFilters, Depends()], auth: authProbeDep, session: DBSession):
    user_id = auth[0] if auth else None
    try:
        return await VacanciesRepository.get_many(session=session, user_id=user_id, pagination=pagination, filters=filters)
    except Exception as e:
        logger.error("list_vacancies VacanciesRepository.get_many")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@vacancies_router.get("/{id}", response_model=PaginatedOut[VacancyCardOut])
async def get_vacancy(id: Annotated[UUID, Path()], auth: authProbeDep, session: DBSession):
    user_id = auth[0] if auth else None
    try:
        return await VacanciesRepository.get_by_id(session=session, id=id, user_id=user_id)
    except Exception as e:
        logger.error("list_vacancies VacanciesRepository.get_by_id")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@vacancies_router.get("/applications", response_model=PaginatedOut[ApplicationOut])
async def list_applications(pagination: Annotated[Pagination, Depends()], filters: Annotated[ApplicationFilters, Depends()], session: DBSession):
    try:
        return await VacanciesRepository.get_applications(session=session, pagination=pagination, filters=filters)
    except Exception as e:
        logger.error("list_applications VacanciesRepository.get_applications")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@vacancies_router.get("/applications/{id}", response_model=PaginatedOut[ApplicationOut])
async def get_application(id: Annotated[UUID, Path()], session: DBSession):
    try:
        return await VacanciesRepository.get_application_by_id(session=session, id=id)
    except Exception as e:
        logger.error("list_applications VacanciesRepository.get_applications")
        pprint(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")
