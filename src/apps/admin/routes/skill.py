from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse, SkillRequest, SkillResponse
from src.apps.skills.repositories import SkillRepository
from src.core.database import sessionDep

from .router import admin_router


@admin_router.post(
    "/skills", status_code=status.HTTP_201_CREATED, response_model=SkillResponse
)
async def create_skill(session: sessionDep, schm: SkillRequest):
    return await SkillRepository.create(session, name=schm.name)


@admin_router.patch("/skills/{skill_id}", response_model=MessageResponse)
async def update_skill(session: sessionDep, skill_id: UUID, schm: SkillRequest):
    await SkillRepository.update(session, skill_id, schm.name)
    await session.commit()
    return MessageResponse(message="Skill updated successfully")


@admin_router.delete(
    "/skills/{skill_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_skill(session: sessionDep, skill_id: UUID):
    await SkillRepository.delete(session, skill_id)
    await session.commit()
