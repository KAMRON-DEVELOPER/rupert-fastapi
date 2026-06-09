from fastapi import APIRouter, HTTPException, status

from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.stats.schemas import StatsResponse
from src.apps.users.repositories.user import UsersRepository
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.core.database import sessionDep
from src.core.logger import logger

stats_router = APIRouter()


@stats_router.get("/", response_model=StatsResponse)
async def stats(session: sessionDep):
    try:
        users = await UsersRepository.get_stats(session)
        vacancies = await VacanciesRepository.get_stats(session)
        companies = await CompaniesRepository.get_stats(session)
    except Exception as e:
        logger.error(f"<stats>: {e}")
        raise HTTPException(status_code=status.HTTP)

    return StatsResponse(users=users, vacancies=vacancies, companies=companies)
