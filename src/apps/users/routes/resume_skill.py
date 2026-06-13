from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import (
    MessageResponse,
    PaginatedResponse,
    paginationDep,
)
from src.apps.shared.schemas.skill import (
    SkillLinkCreateRequest,
    SkillLinkResponse,
    SkillLinkUpdateRequest,
)
from src.apps.users.repositories.resume_skill import ResumeSkillsRepository
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.get(
    "/resumes/{resume_id}/skills",
    response_model=PaginatedResponse[SkillLinkResponse],
)
async def list_resume_skills(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    pagination: paginationDep,
):
    user_id, _, _ = auth
    records = await ResumeSkillsRepository.get_many(
        session, user_id, resume_id, pagination.offset, pagination.limit
    )
    return records


@users_router.post(
    "/resumes/{resume_id}/skills",
    response_model=SkillLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resume_skill(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    schm: SkillLinkCreateRequest,
):
    user_id, _, _ = auth

    record = await ResumeSkillsRepository.create(
        session, user_id, resume_id, schm
    )
    await session.commit()
    return SkillLinkResponse.model_validate(record)


@users_router.patch(
    "/resumes/{resume_id}/skills/{skill_link_id}",
    response_model=SkillLinkResponse,
)
async def update_resume_skill(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    skill_link_id: UUID,
    schm: SkillLinkUpdateRequest,
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
    return SkillLinkResponse.model_validate(record)


@users_router.delete(
    "/resumes/{resume_id}/skills/{skill_link_id}",
    response_model=MessageResponse,
)
async def delete_resume_skill(
    auth: authDep, session: sessionDep, resume_id: UUID, skill_link_id: UUID
):
    user_id, _, _ = auth

    await ResumeSkillsRepository.delete(
        session, user_id, resume_id, skill_link_id
    )
    await session.commit()
    return MessageResponse(message="Resume skills deleted successfully")
