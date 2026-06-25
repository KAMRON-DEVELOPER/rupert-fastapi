from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.users.repositories.resume import ResumesRepository
from src.apps.companies.models import CompanyModel
from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.apps.shared.schemas.enums import (
    ApplicationStatus,
    CompanyMemberRole,
    VacancyStatus,
)
from src.apps.users.models import ResumeModel, UserModel
from src.apps.vacancies.models import ApplicationModel, VacancyModel
from src.apps.vacancies.repositories.vacancy import VacanciesRepository
from src.apps.vacancies.schemas.application import (
    ApplicationDetailResponse,
    applicationListDep,
)
from src.core.logger import logger

OPTIONS = (
    selectinload(ApplicationModel.vacancy).selectinload(VacancyModel.country),
    selectinload(ApplicationModel.vacancy).selectinload(VacancyModel.city),
    selectinload(ApplicationModel.vacancy)
    .selectinload(VacancyModel.company)
    .selectinload(CompanyModel.country),
    selectinload(ApplicationModel.vacancy)
    .selectinload(VacancyModel.company)
    .selectinload(CompanyModel.city),
    selectinload(ApplicationModel.resume).selectinload(ResumeModel.country),
    selectinload(ApplicationModel.resume).selectinload(ResumeModel.city),
    selectinload(ApplicationModel.applicant).selectinload(UserModel.country),
    selectinload(ApplicationModel.applicant).selectinload(UserModel.city),
)


class ApplicationsRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        applicant_id: UUID,
        vacancy_id: UUID,
        resume_id: UUID | None = None,
        cover_letter: str | None = None,
    ) -> ApplicationModel:
        vacancy = await VacanciesRepository.get(session, vacancy_id)
        if vacancy.status != VacancyStatus.open:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vacancy is not open for applications",
            )

        if resume_id:
            await ResumesRepository.get(session, applicant_id, resume_id)

        record = ApplicationModel(
            applicant_id=applicant_id,
            vacancy_id=vacancy_id,
            resume_id=resume_id,
            cover_letter=cover_letter,
        )

        try:
            session.add(record)
            await session.flush()
            return record
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ApplicationsRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already exists or references invalid data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ApplicationsRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating application",
            )

    @staticmethod
    async def update(
        session: AsyncSession,
        *,
        applicant_id: UUID,
        vacancy_id: UUID,
        resume_id: UUID | None = None,
        cover_letter: str | None = None,
    ) -> ApplicationModel:
        stmt = (
            update(ApplicationModel)
            .where(
                ApplicationModel.applicant_id == applicant_id,
                ApplicationModel.vacancy_id == vacancy_id,
            )
            .values(resume_id=resume_id, cover_letter=cover_letter)
            .returning(ApplicationModel)
            .options(*OPTIONS)
        )

        if resume_id:
            await ResumesRepository.get(session, applicant_id, resume_id)

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ApplicationsRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application data is invalid",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ApplicationsRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating application",
            )

    @staticmethod
    async def get(session: AsyncSession, id: UUID) -> ApplicationModel:
        stmt = (
            select(ApplicationModel)
            .options(*OPTIONS)
            .where(ApplicationModel.id == id)
            .execution_options(populate_existing=True)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            logger.error("[ApplicationsRepository] get: Application not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        except MultipleResultsFound:
            logger.error(
                f"[ApplicationsRepository] get: multiple rows for id={id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Multiple application rows found",
            )
        except Exception as e:
            logger.error(f"[ApplicationsRepository] get: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve application",
            )

    @staticmethod
    async def get_optional(
        session: AsyncSession, id: UUID
    ) -> ApplicationModel | None:
        stmt = (
            select(ApplicationModel)
            .options(*OPTIONS)
            .where(ApplicationModel.id == id)
            .execution_options(populate_existing=True)
        )

        try:
            return await session.scalar(stmt)
        except Exception as e:
            logger.error(f"[ApplicationsRepository] get_optional: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve application",
            )

    @staticmethod
    async def get_many(
        session: AsyncSession,
        pagination: paginationDep,
        filters: applicationListDep,
    ) -> PaginatedResponse[ApplicationDetailResponse]:
        stmt = select(ApplicationModel)

        if filters:
            if filters.vacancy_id:
                stmt = stmt.where(
                    ApplicationModel.vacancy_id == filters.vacancy_id
                )
            if filters.applicant_id:
                stmt = stmt.where(
                    ApplicationModel.applicant_id == filters.applicant_id
                )
            if filters.status:
                stmt = stmt.where(ApplicationModel.status == filters.status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.options(
            selectinload(ApplicationModel.vacancy).selectinload(
                VacancyModel.country
            ),
            selectinload(ApplicationModel.vacancy).selectinload(
                VacancyModel.city
            ),
            selectinload(ApplicationModel.vacancy)
            .selectinload(VacancyModel.company)
            .selectinload(CompanyModel.country),
            selectinload(ApplicationModel.vacancy)
            .selectinload(VacancyModel.company)
            .selectinload(CompanyModel.city),
            selectinload(ApplicationModel.resume).selectinload(
                ResumeModel.country
            ),
            selectinload(ApplicationModel.resume).selectinload(
                ResumeModel.city
            ),
            selectinload(ApplicationModel.applicant).selectinload(
                UserModel.country
            ),
            selectinload(ApplicationModel.applicant).selectinload(
                UserModel.city
            ),
        ).order_by(ApplicationModel.created_at.desc())
        stmt = stmt.execution_options(populate_existing=True)

        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)

        res = await session.scalars(stmt)
        data = cast(list[ApplicationDetailResponse], list(res.all()))
        return PaginatedResponse(data=data, total=total)

    @staticmethod
    async def update_application_status(
        session: AsyncSession,
        application_id: UUID,
        application_status: ApplicationStatus,
        recruiter_note: str | None = None,
        user_id: UUID | None = None,
    ) -> ApplicationModel | None:
        application = await ApplicationsRepository.get(session, application_id)
        if user_id:
            await CompaniesRepository.ensure_member(
                session,
                user_id,
                application.vacancy.company_id,
                (CompanyMemberRole.owner, CompanyMemberRole.recruiter),
            )

        try:
            values: dict = {"status": application_status}
            if recruiter_note is not None:
                values["recruiter_note"] = recruiter_note

            stmt = (
                update(ApplicationModel)
                .where(ApplicationModel.id == application_id)
                .values(values)
                .returning(ApplicationModel.id)
            )
            await session.scalar(stmt)
            await session.flush()
            return await ApplicationsRepository.get(session, application_id)
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(
                f"[ApplicationsRepository] update_application_status: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating application",
            )
