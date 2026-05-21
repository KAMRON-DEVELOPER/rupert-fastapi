from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import SkillRequest
from src.apps.skills.repositories import SkillRepository
from src.core.database import sessionDep

from .router import admin_router


@admin_router.post("/skills", status_code=status.HTTP_201_CREATED)
async def create_skill(session: sessionDep, schm=SkillRequest):
    await SkillRepository.create(session, name=schm.name)


@admin_router.patch("/skills/{skill_id}")
async def update_skill(
    session: sessionDep,
    skill_id: UUID,
    schm: SkillRequest,
):
    await SkillRepository.update(session, skill_id, schm.name)
