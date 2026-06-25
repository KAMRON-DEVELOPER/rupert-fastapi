from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.shared.schemas import PaginatedResponse
from src.apps.shared.schemas.enums import CompanyMemberRole
from src.apps.vacancies.models import VacancySkillLink
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.apps.vacancies.schemas.skill_links import VacancySkillLinkResponse
from src.core.logger import logger


class VacancySkillsRepository:
    @staticmethod
    async def create(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID, values: dict
    ):
        vacancy = await VacanciesRepository.get(session, vacancy_id)
        await CompaniesRepository.ensure_member(
            session,
            user_id,
            vacancy.company_id,
            (CompanyMemberRole.owner, CompanyMemberRole.recruiter),
        )

        try:
            record = VacancySkillLink(vacancy_id=vacancy_id, **values)
            session.add(record)
            await session.flush()
            return await VacanciesRepository.get_skill_link_by_id(
                session, vacancy_id, record.id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[VacancySkillsRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vacancy skill already exists or references invalid skill",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacancySkillsRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating vacancy skill",
            )

    @staticmethod
    async def update(
        session: AsyncSession,
        user_id: UUID,
        vacancy_id: UUID,
        link_id: UUID,
        values: dict,
    ):
        vacancy = await VacanciesRepository.get(session, vacancy_id)
        await CompaniesRepository.ensure_member(
            session,
            user_id,
            vacancy.company_id,
            (CompanyMemberRole.owner, CompanyMemberRole.recruiter),
        )
        await VacanciesRepository.get_skill_link_by_id(
            session, vacancy_id, link_id
        )

        try:
            if values:
                stmt = (
                    update(VacancySkillLink)
                    .where(
                        VacancySkillLink.id == link_id,
                        VacancySkillLink.vacancy_id == vacancy_id,
                    )
                    .values(values)
                    .returning(VacancySkillLink.id)
                )
                await session.scalar(stmt)
                await session.flush()

            return await VacanciesRepository.get_skill_link_by_id(
                session, vacancy_id, link_id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[VacancySkillsRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vacancy skill data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacancySkillsRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating vacancy skill",
            )

    @staticmethod
    async def delete(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID, link_id: UUID
    ):
        vacancy = await VacanciesRepository.get(session, vacancy_id)
        await CompaniesRepository.ensure_member(
            session,
            user_id,
            vacancy.company_id,
            (CompanyMemberRole.owner, CompanyMemberRole.recruiter),
        )

        stmt = (
            delete(VacancySkillLink)
            .where(
                VacancySkillLink.id == link_id,
                VacancySkillLink.vacancy_id == vacancy_id,
            )
            .returning(VacancySkillLink.id)
        )

        try:
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vacancy skill link not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacancySkillsRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting vacancy skill",
            )

    @staticmethod
    async def get(
        session: AsyncSession, vacancy_id: UUID, link_id: UUID
    ) -> VacancySkillLink:
        stmt = (
            select(VacancySkillLink)
            .options(selectinload(VacancySkillLink.skill))
            .where(
                VacancySkillLink.id == link_id,
                VacancySkillLink.vacancy_id == vacancy_id,
            )
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy skill link not found",
            )
        except Exception as e:
            logger.error(f"[VacancySkillsRepository] get: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving vacancy skill",
            )

    @staticmethod
    async def get_optional(
        session: AsyncSession, vacancy_id: UUID, link_id: UUID
    ) -> VacancySkillLink | None:
        stmt = (
            select(VacancySkillLink)
            .options(selectinload(VacancySkillLink.skill))
            .where(
                VacancySkillLink.id == link_id,
                VacancySkillLink.vacancy_id == vacancy_id,
            )
        )

        try:
            return await session.scalar(stmt)
        except Exception as e:
            logger.error(f"[VacancySkillsRepository] get_optional: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving vacancy skill",
            )

    @staticmethod
    async def get_many(
        session: AsyncSession,
        vacancy_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedResponse[VacancySkillLinkResponse]:
        stmt = (
            select(VacancySkillLink)
            .options(selectinload(VacancySkillLink.skill))
            .where(VacancySkillLink.vacancy_id == vacancy_id)
            .order_by(VacancySkillLink.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total_stmt = select(func.count(VacancySkillLink.id)).where(
            VacancySkillLink.vacancy_id == vacancy_id
        )

        try:
            records = (await session.scalars(stmt)).all()
            data = [VacancySkillLinkResponse.model_validate(r) for r in records]
            total = await session.scalar(total_stmt) or 0

            return PaginatedResponse(data=data, total=total)
        except Exception as e:
            logger.error(f"[VacancySkillsRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving vacancy skills",
            )
