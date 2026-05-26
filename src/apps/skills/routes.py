from fastapi import APIRouter

from src.apps.shared.schemas import paginationDep
from src.apps.skills.repositories import SkillRepository
from src.core.database import sessionDep

skills_router = APIRouter()


@skills_router.get("/")
async def list_skills(session: sessionDep, pagination: paginationDep):
    return await SkillRepository.get_many(
        session, pagination.limit, pagination.offset
    )
