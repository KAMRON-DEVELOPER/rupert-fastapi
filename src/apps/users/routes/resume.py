from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse
from src.apps.users.repositories.resume import ResumesRepository
from src.apps.users.schemas.resume import (
    ResumeCreateRequest,
    ResumeResponse,
    ResumeUpdateRequest,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.get("/resumes", response_model=list[ResumeResponse])
async def list_resumes(auth: authDep, session: sessionDep):
    user_id, _, _ = auth
    records = await ResumesRepository.get_many(session, user_id)
    return [ResumeResponse.model_validate(record) for record in records]


@users_router.post(
    "/resumes",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resume(
    auth: authDep, session: sessionDep, schm: ResumeCreateRequest
):
    user_id, _, _ = auth
    payload = schm.model_dump()
    skills = payload.pop("skills")
    record = await ResumesRepository.create(session, user_id, payload, skills)
    await session.commit()
    return ResumeResponse.model_validate(record)


@users_router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume(auth: authDep, session: sessionDep, resume_id: UUID):
    user_id, _, _ = auth
    record = await ResumesRepository.get_by_id_and_user_id(
        session, user_id, resume_id
    )
    return ResumeResponse.model_validate(record)


@users_router.patch("/resumes/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    auth: authDep,
    session: sessionDep,
    resume_id: UUID,
    schm: ResumeUpdateRequest,
):
    user_id, _, _ = auth
    payload = schm.model_dump(exclude_unset=True)
    record = await ResumesRepository.update(
        session, user_id, resume_id, payload
    )
    await session.commit()
    return ResumeResponse.model_validate(record)


@users_router.delete(
    "/resumes/{resume_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_resume(auth: authDep, session: sessionDep, resume_id: UUID):
    user_id, _, _ = auth
    await ResumesRepository.delete(session, user_id, resume_id)
    await session.commit()
    return MessageResponse(message="Resume deleted successfully")
