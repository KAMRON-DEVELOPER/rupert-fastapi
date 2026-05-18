from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse
from src.apps.users.repositories.resume_skill import ResumeSkillsRepository
from src.apps.users.schemas.skill_links import (
    ResumeSkillLinkRequest,
    ResumeSkillLinkResponse,
    ResumeSkillLinkUpdateRequest,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.post(
    "/resumes/{resume_id}/skills",
    response_model=ResumeSkillLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resume_skill(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    schm: ResumeSkillLinkRequest,
):
    user_id, _, _ = auth

    record = await ResumeSkillsRepository.create(
        session, user_id, resume_id, schm.model_dump()
    )
    await session.commit()
    return ResumeSkillLinkResponse.model_validate(record)


@users_router.patch(
    "/resumes/{resume_id}/skills/{skill_link_id}",
    response_model=ResumeSkillLinkResponse,
)
async def update_resume_skill(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    skill_link_id: UUID,
    schm: ResumeSkillLinkUpdateRequest,
):
    user_id, _, _ = auth

    record = await ResumeSkillsRepository.update(
        session,
        user_id,
        resume_id,
        skill_link_id,
        schm.model_dump(exclude_unset=True),
    )
    await session.commit()
    return ResumeSkillLinkResponse.model_validate(record)


@users_router.delete(
    "/resumes/{resume_id}/skills/{skill_link_id}",
    response_model=MessageResponse,
)
async def delete_resume_skill(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    skill_link_id: UUID,
):
    user_id, _, _ = auth

    await ResumeSkillsRepository.delete(
        session, user_id, resume_id, skill_link_id
    )
    await session.commit()
    return MessageResponse(message="Resume skill deleted successfully")
