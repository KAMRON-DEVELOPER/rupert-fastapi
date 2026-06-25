from typing import Annotated
from uuid import UUID

from fastapi import Path, status

from src.apps.shared.schemas import (
    MessageResponse,
    PaginatedResponse,
    paginationDep,
)
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.apps.vacancies.schemas.vacancy import (
    VacancyCreateRequest,
    VacancyDetail,
    VacancySummary,
    VacancyUpdateRequest,
    vacancyListDep,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep, authProbeDep

from .router import vacancies_router


@vacancies_router.post(
    "/companies/{company_id}",
    response_model=VacancyDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_vacancy(
    auth: authDep,
    session: sessionDep,
    company_id: UUID,
    schm: VacancyCreateRequest,
):
    user_id, _, _ = auth
    record = await VacanciesRepository.create(
        session, user_id, company_id, schm.model_dump(mode="json")
    )
    await session.commit()
    return VacancyDetail.model_validate(record)


@vacancies_router.patch("/{id}", response_model=VacancyDetail)
async def update_vacancy(
    auth: authDep,
    session: sessionDep,
    id: Annotated[UUID, Path()],
    schm: VacancyUpdateRequest,
):
    user_id, _, _ = auth
    record = await VacanciesRepository.update(
        session, user_id, id, schm.model_dump(mode="json", exclude_unset=True)
    )
    await session.commit()
    return VacancyDetail.model_validate(record)


@vacancies_router.delete(
    "/{id}", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def delete_vacancy(
    auth: authDep, session: sessionDep, id: Annotated[UUID, Path()]
):
    user_id, _, _ = auth
    await VacanciesRepository.delete(session, user_id, id)
    await session.commit()
    return MessageResponse(message="Vacancy deleted successfully")


@vacancies_router.get("/", response_model=PaginatedResponse[VacancySummary])
async def list_vacancies(
    auth: authProbeDep,
    pagination: paginationDep,
    filters: vacancyListDep,
    session: sessionDep,
):
    user_id = auth[0] if auth else None
    return await VacanciesRepository.get_many(
        session=session, user_id=user_id, pagination=pagination, filters=filters
    )


@vacancies_router.get("/{id}", response_model=VacancyDetail)
async def get_vacancy(
    id: Annotated[UUID, Path()], auth: authProbeDep, session: sessionDep
):
    user_id = auth[0] if auth else None
    record = await VacanciesRepository.get(
        session=session, id=id, user_id=user_id
    )
    return VacancyDetail.model_validate(record)


@vacancies_router.post(
    "/{id}/save",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_vacancy(
    auth: authDep, session: sessionDep, id: Annotated[UUID, Path()]
):
    user_id, _, _ = auth
    await VacanciesRepository.save_vacancy(session, user_id, id)
    await session.commit()
    return MessageResponse(message="Vacancy saved successfully")


@vacancies_router.delete(
    "/{id}/save", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def unsave_vacancy(
    auth: authDep, session: sessionDep, id: Annotated[UUID, Path()]
):
    user_id, _, _ = auth
    await VacanciesRepository.unsave_vacancy(session, user_id, id)
    await session.commit()
    return MessageResponse(message="Vacancy unsaved successfully")
