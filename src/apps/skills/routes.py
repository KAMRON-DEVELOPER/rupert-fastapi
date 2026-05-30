from fastapi import APIRouter

from src.apps.shared.schemas import (
    PaginatedResponse,
    SkillResponse,
    paginationDep,
)
from src.apps.skills.repositories import SkillRepository
from src.core.database import sessionDep

skills_router = APIRouter()


@skills_router.get("/", response_model=PaginatedResponse[SkillResponse])
async def list_skills(session: sessionDep, pagination: paginationDep):
    return await SkillRepository.get_many(
        session, pagination.limit, pagination.offset
    )
