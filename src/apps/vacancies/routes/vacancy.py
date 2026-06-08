from typing import Annotated
from uuid import UUID

from fastapi import Path, status

from src.apps.shared.schemas import (
    MessageResponse,
    PaginatedResponse,
    paginationDep,
)
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.apps.vacancies.schemas.application import (
    ApplicationDetail,
    ApplicationRequest,
    ApplicationStatusUpdateRequest,
    ApplicationSummary,
    applicationListDep,
)
from src.apps.vacancies.schemas.skill_links import (
    VacancySkillLinkRequest,
    VacancySkillLinkResponse,
    VacancySkillLinkUpdateRequest,
)
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


@vacancies_router.get("/", response_model=PaginatedResponse[VacancySummary])
async def list_vacancies(
    pagination: paginationDep,
    filters: vacancyListDep,
    auth: authProbeDep,
    session: sessionDep,
):
    user_id = auth[0] if auth else None
    return await VacanciesRepository.get_many(
        session=session, user_id=user_id, pagination=pagination, filters=filters
    )


@vacancies_router.get(
    "/applications", response_model=PaginatedResponse[ApplicationSummary]
)
async def list_applications(
    pagination: paginationDep, filters: applicationListDep, session: sessionDep
):
    return await VacanciesRepository.get_applications(
        session=session, pagination=pagination, filters=filters
    )


@vacancies_router.post(
    "/applications",
    response_model=ApplicationDetail,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_vacancy(
    auth: authDep, session: sessionDep, schm: ApplicationRequest
):
    user_id, _, _ = auth
    record = await VacanciesRepository.apply_to_vacancy(
        session, user_id, schm.model_dump()
    )
    await session.commit()
    return ApplicationDetail.model_validate(record)


@vacancies_router.get("/applications/{id}", response_model=ApplicationDetail)
async def get_application(id: Annotated[UUID, Path()], session: sessionDep):
    record = await VacanciesRepository.get_application_by_id(
        session=session, id=id
    )
    return ApplicationDetail.model_validate(record)


@vacancies_router.patch("/applications/{id}", response_model=ApplicationDetail)
async def update_application_status(
    auth: authDep,
    session: sessionDep,
    id: Annotated[UUID, Path()],
    schm: ApplicationStatusUpdateRequest,
):
    user_id, _, _ = auth
    record = await VacanciesRepository.update_application_status(
        session=session,
        application_id=id,
        application_status=schm.status,
        recruiter_note=schm.recruiter_note,
        user_id=user_id,
    )
    await session.commit()
    return ApplicationDetail.model_validate(record)


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


@vacancies_router.get("/{id}", response_model=VacancyDetail)
async def get_vacancy(
    id: Annotated[UUID, Path()], auth: authProbeDep, session: sessionDep
):
    user_id = auth[0] if auth else None
    record = await VacanciesRepository.get_by_id(
        session=session, id=id, user_id=user_id
    )
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


@vacancies_router.post(
    "/{vacancy_id}/skills",
    response_model=VacancySkillLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_vacancy_skill(
    auth: authDep,
    session: sessionDep,
    vacancy_id: UUID,
    schm: VacancySkillLinkRequest,
):
    user_id, _, _ = auth
    record = await VacanciesRepository.create_skill_link(
        session, user_id, vacancy_id, schm.model_dump()
    )
    await session.commit()
    return VacancySkillLinkResponse.model_validate(record)


@vacancies_router.patch(
    "/{vacancy_id}/skills/{skill_link_id}",
    response_model=VacancySkillLinkResponse,
)
async def update_vacancy_skill(
    auth: authDep,
    session: sessionDep,
    vacancy_id: UUID,
    skill_link_id: UUID,
    schm: VacancySkillLinkUpdateRequest,
):
    user_id, _, _ = auth
    record = await VacanciesRepository.update_skill_link(
        session,
        user_id,
        vacancy_id,
        skill_link_id,
        schm.model_dump(exclude_unset=True),
    )
    await session.commit()
    return VacancySkillLinkResponse.model_validate(record)


@vacancies_router.delete(
    "/{vacancy_id}/skills/{skill_link_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_vacancy_skill(
    auth: authDep, session: sessionDep, vacancy_id: UUID, skill_link_id: UUID
):
    user_id, _, _ = auth
    await VacanciesRepository.delete_skill_link(
        session, user_id, vacancy_id, skill_link_id
    )
    await session.commit()
    return MessageResponse(message="Vacancy skill deleted successfully")


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
