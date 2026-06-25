from uuid import UUID

from fastapi import status

from src.apps.shared.schemas import MessageResponse
from src.apps.vacancies.repositories.vacancy_skill import (
    VacancySkillsRepository,
)
from src.apps.vacancies.schemas.skill_links import (
    VacancySkillLinkRequest,
    VacancySkillLinkResponse,
    VacancySkillLinkUpdateRequest,
)
from src.core.database import sessionDep
from src.dependencies.proactive_refresh import authDep

from .router import vacancies_router


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
    record = await VacancySkillsRepository.create(
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
    record = await VacancySkillsRepository.update(
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
    await VacancySkillsRepository.delete(
        session, user_id, vacancy_id, skill_link_id
    )
    await session.commit()
    return MessageResponse(message="Vacancy skill deleted successfully")
