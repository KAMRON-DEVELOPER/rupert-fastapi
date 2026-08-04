from typing import Annotated
from uuid import UUID

from fastapi import Path, status

from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.apps.vacancies.repositories.application import ApplicationsRepository
from src.apps.vacancies.schemas.application import (
    ApplicationCreateRequest,
    ApplicationDetailResponse,
    ApplicationStatusUpdateRequest,
    ApplicationSummaryResponse,
    ApplicationUpdateRequest,
    applicationListDep,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import vacancies_router


@vacancies_router.post(
    "/{vacancy_id}/applications",
    response_model=ApplicationDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    auth: authDep,
    session: sessionDep,
    vacancy_id: UUID,
    schm: ApplicationCreateRequest,
):
    user_id, _, _ = auth
    record = await ApplicationsRepository.create(
        session,
        applicant_id=user_id,
        vacancy_id=vacancy_id,
        resume_id=schm.resume_id,
        cover_letter=schm.cover_letter,
    )
    await session.commit()
    return ApplicationDetailResponse.model_validate(record)


@vacancies_router.patch(
    "/{vacancy_id}/applications", response_model=ApplicationDetailResponse
)
async def update(
    auth: authDep,
    session: sessionDep,
    vacancy_id: UUID,
    schm: ApplicationUpdateRequest,
):
    user_id, _, _ = auth
    record = await ApplicationsRepository.update(
        session,
        applicant_id=user_id,
        vacancy_id=vacancy_id,
        resume_id=schm.resume_id,
        cover_letter=schm.cover_letter,
    )
    await session.commit()
    return ApplicationDetailResponse.model_validate(record)


@vacancies_router.patch(
    "/{vacancy_id}/applications/{application_id}",
    response_model=ApplicationDetailResponse,
)
async def update_application_status(
    auth: authDep,
    session: sessionDep,
    application_id: Annotated[UUID, Path()],
    vacancy_id: UUID,
    schm: ApplicationStatusUpdateRequest,
):
    user_id, _, _ = auth
    record = await ApplicationsRepository.update_application_status(
        session=session,
        vacancy_id=vacancy_id,
        application_id=application_id,
        application_status=schm.status,
        recruiter_note=schm.recruiter_note,
        user_id=user_id,
    )
    await session.commit()
    return ApplicationDetailResponse.model_validate(record)


@vacancies_router.get(
    "/{vacancy_id}/applications",
    response_model=PaginatedResponse[ApplicationSummaryResponse],
)
async def list_applications(
    session: sessionDep,
    pagination: paginationDep,
    filters: applicationListDep,
    vacancy_id: UUID,
):
    return await ApplicationsRepository.get_many(
        session=session,
        pagination=pagination,
        vacancy_id=vacancy_id,
        filters=filters,
    )


@vacancies_router.get(
    "/{vacancy_id}/applications/{application_id}",
    response_model=ApplicationDetailResponse,
)
async def get_application(
    application_id: Annotated[UUID, Path()],
    session: sessionDep,
    vacancy_id: UUID,
):
    record = await ApplicationsRepository.get(
        session=session, vacancy_id=vacancy_id, application_id=application_id
    )
    return ApplicationDetailResponse.model_validate(record)
