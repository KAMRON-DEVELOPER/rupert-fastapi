from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse
from src.apps.users.repositories.work_experience import (
    WorkExperiencesRepository,
)
from src.apps.users.schemas.work_experience import (
    WorkExperienceRequest,
    WorkExperienceResponse,
    WorkExperienceUpdateRequest,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import users_router


@users_router.get(
    "/work-experiences", response_model=list[WorkExperienceResponse]
)
async def list_work_experiences(auth: authDep, session: sessionDep):
    user_id, _, _ = auth
    records = await WorkExperiencesRepository.list_by_user_id(session, user_id)
    return [WorkExperienceResponse.model_validate(record) for record in records]


@users_router.post(
    "/work-experiences",
    response_model=WorkExperienceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_work_experience(
    auth: authDep, session: sessionDep, schm: WorkExperienceRequest
):
    user_id, _, _ = auth
    record = await WorkExperiencesRepository.create(
        session, user_id, schm.model_dump()
    )
    await session.commit()
    return WorkExperienceResponse.model_validate(record)


@users_router.patch(
    "/work-experiences/{work_experience_id}",
    response_model=WorkExperienceResponse,
)
async def update_work_experience(
    auth: authDep,
    session: sessionDep,
    work_experience_id: UUID,
    schm: WorkExperienceUpdateRequest,
):
    user_id, _, _ = auth
    record = await WorkExperiencesRepository.update(
        session,
        user_id,
        work_experience_id,
        schm.model_dump(exclude_unset=True),
    )
    await session.commit()
    return WorkExperienceResponse.model_validate(record)


@users_router.delete(
    "/work-experiences/{work_experience_id}",
    response_model=MessageResponse,
)
async def delete_work_experience(
    auth: authDep, session: sessionDep, work_experience_id: UUID
):
    user_id, _, _ = auth
    await WorkExperiencesRepository.delete(session, user_id, work_experience_id)
    await session.commit()
    return MessageResponse(message="Work experience deleted successfully")
