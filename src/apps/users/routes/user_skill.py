from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse
from src.apps.shared.schemas.skill import (
    SkillLinkCreateRequest,
    SkillLinkResponse,
    SkillLinkUpdateRequest,
)
from src.apps.users.repositories.user_skill import UserSkillsRepository
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.get("/skills", response_model=list[SkillLinkResponse])
async def list_user_skills(auth: authDep, session: sessionDep):
    user_id, _, _ = auth
    records = await UserSkillsRepository.list_by_user_id(session, user_id)
    return [SkillLinkResponse.model_validate(record) for record in records]


@users_router.post(
    "/skills",
    response_model=SkillLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_skill(
    auth: authDep, session: sessionDep, schm: SkillLinkCreateRequest
):
    user_id, _, _ = auth
    record = await UserSkillsRepository.create(
        session, user_id, schm.model_dump()
    )
    await session.commit()
    return SkillLinkResponse.model_validate(record)


@users_router.patch("/skills/{skill_link_id}", response_model=SkillLinkResponse)
async def update_user_skill(
    auth: authDep,
    session: sessionDep,
    skill_link_id: UUID,
    schm: SkillLinkUpdateRequest,
):
    user_id, _, _ = auth
    record = await UserSkillsRepository.update(
        session, user_id, skill_link_id, schm.model_dump(exclude_unset=True)
    )
    await session.commit()
    return SkillLinkResponse.model_validate(record)


@users_router.delete(
    "/skills/{skill_link_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_user_skill(
    auth: authDep, session: sessionDep, skill_link_id: UUID
):
    user_id, _, _ = auth
    await UserSkillsRepository.delete(session, user_id, skill_link_id)
    await session.commit()
    return MessageResponse(message="User skill deleted successfully")
