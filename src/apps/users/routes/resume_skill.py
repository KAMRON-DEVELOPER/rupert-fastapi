from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse
from src.apps.shared.schemas.skill import (
    SkillLinkBatchCreateRequest,
    SkillLinkBatchDeleteRequest,
    SkillLinkBatchUpdateRequest,
    SkillLinkResponse,
)
from src.apps.users.repositories.resume_skill import ResumeSkillsRepository
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.post(
    "/resumes/{resume_id}/skills",
    response_model=list[SkillLinkResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_resume_skills(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    schm: SkillLinkBatchCreateRequest,
):
    user_id, _, _ = auth

    records = await ResumeSkillsRepository.create_batch(
        session, user_id, resume_id, [s.model_dump() for s in schm.skills]
    )
    await session.commit()
    return [SkillLinkResponse.model_validate(r) for r in records]


@users_router.patch(
    "/resumes/{resume_id}/skills",
    response_model=list[SkillLinkResponse],
)
async def update_resume_skills(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    schm: SkillLinkBatchUpdateRequest,
):
    user_id, _, _ = auth

    records = await ResumeSkillsRepository.update_batch(
        session,
        user_id,
        resume_id,
        [s.model_dump(exclude_unset=True) for s in schm.skills],
    )
    await session.commit()
    return [SkillLinkResponse.model_validate(r) for r in records]


@users_router.delete(
    "/resumes/{resume_id}/skills",
    response_model=MessageResponse,
)
async def delete_resume_skills(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    schm: SkillLinkBatchDeleteRequest,
):
    user_id, _, _ = auth

    await ResumeSkillsRepository.delete_batch(
        session, user_id, resume_id, schm.skill_link_ids
    )
    await session.commit()
    return MessageResponse(message="Resume skills deleted successfully")
