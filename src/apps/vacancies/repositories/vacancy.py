from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.companies.models import CompanyMemberModel, CompanyModel
from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.shared.schemas import (
    PaginatedResponse,
    PermissionSchema,
    paginationDep,
)
from src.apps.shared.schemas.enums import CompanyMemberRole, VacancyStatus
from src.apps.stats.schemas import (
    SpecializationBucket,
    VacanciesStatsResponse,
    VacancyStatusBucket,
)
from src.apps.vacancies.models import (
    ApplicationModel,
    SavedVacancyModel,
    VacancyModel,
    VacancySkillLink,
)
from src.apps.vacancies.schemas.vacancy import VacancySummary, vacancyListDep
from src.core.helpers import percentage
from src.core.logger import logger


class VacanciesRepository:
    @staticmethod
    async def create(
        session: AsyncSession, user_id: UUID, company_id: UUID, data: dict
    ) -> VacancyModel:
        await CompaniesRepository.ensure_member(
            session,
            user_id,
            company_id,
            (CompanyMemberRole.owner, CompanyMemberRole.recruiter),
        )

        skills_data: list[dict] = data.pop("skills", [])

        try:
            vacancy = VacancyModel(company_id=company_id, **data)
            session.add(vacancy)
            await session.flush()

            await VacanciesRepository._replace_skills(
                session, vacancy.id, skills_data
            )
            await session.flush()
            return await VacanciesRepository.get(session, vacancy.id, user_id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vacancy data is invalid or contains duplicate skills",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating vacancy",
            )

    @staticmethod
    async def update(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID, data: dict
    ) -> VacancyModel:
        vacancy = await VacanciesRepository.get(session, vacancy_id, user_id)
        await CompaniesRepository.ensure_member(
            session,
            user_id,
            vacancy.company_id,
            (CompanyMemberRole.owner, CompanyMemberRole.recruiter),
        )

        skills = data.pop("skills", None)

        try:
            if data:
                stmt = (
                    update(VacancyModel)
                    .where(VacancyModel.id == vacancy_id)
                    .values(data)
                    .returning(VacancyModel.id)
                )
                await session.scalar(stmt)

            if skills is not None:
                await VacanciesRepository._replace_skills(
                    session, vacancy_id, skills
                )

            await session.flush()
            return await VacanciesRepository.get(session, vacancy_id, user_id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vacancy data is invalid or contains duplicate skills",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating vacancy",
            )

    @staticmethod
    async def delete(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID
    ) -> bool:
        vacancy = await VacanciesRepository.get(session, vacancy_id, user_id)
        await CompaniesRepository.ensure_member(
            session,
            user_id,
            vacancy.company_id,
            (CompanyMemberRole.owner, CompanyMemberRole.recruiter),
        )

        try:
            await session.delete(vacancy)
            await session.flush()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting vacancy",
            )

    @staticmethod
    async def get_many(
        session: AsyncSession,
        pagination: paginationDep,
        filters: vacancyListDep,
        user_id: UUID | None = None,
    ) -> PaginatedResponse[VacancySummary]:
        stmt = (
            select(VacancyModel)
            .options(
                selectinload(VacancyModel.country),
                selectinload(VacancyModel.city),
                selectinload(VacancyModel.company).selectinload(
                    CompanyModel.country
                ),
                selectinload(VacancyModel.company).selectinload(
                    CompanyModel.city
                ),
            )
            .execution_options(populate_existing=True)
        )

        if filters:
            if posted_within_days := filters.posted_within_days:
                boundary = datetime.now(UTC) - timedelta(
                    days=posted_within_days
                )
                stmt = stmt.where(VacancyModel.updated_at > boundary)
            if filters.title:
                stmt = stmt.where(
                    VacancyModel.title.ilike(f"%{filters.title}%")
                )
            if filters.submission_type:
                stmt = stmt.where(
                    VacancyModel.submission_type == filters.submission_type
                )
            if filters.specialization:
                stmt = stmt.where(
                    VacancyModel.specialization.in_(filters.specialization)
                )
            if filters.salary_min is not None:
                stmt = stmt.where(VacancyModel.salary_max.is_not(None))
                stmt = stmt.where(VacancyModel.salary_max >= filters.salary_min)
            if filters.salary_max is not None:
                stmt = stmt.where(VacancyModel.salary_min.is_not(None))
                stmt = stmt.where(VacancyModel.salary_min <= filters.salary_max)
            if filters.salary_currency:
                stmt = stmt.where(
                    VacancyModel.salary_currency == filters.salary_currency
                )
            if filters.years_of_experience_min is not None:
                stmt = stmt.where(
                    VacancyModel.years_of_experience_min.is_not(None)
                )
                stmt = stmt.where(
                    VacancyModel.years_of_experience_min
                    >= filters.years_of_experience_min
                )
            if filters.work_format:
                stmt = stmt.where(
                    VacancyModel.work_format == filters.work_format
                )
            if filters.employment_type:
                stmt = stmt.where(
                    VacancyModel.employment_type == filters.employment_type
                )
            if filters.status:
                stmt = stmt.where(VacancyModel.status == filters.status)
            if filters.skill_ids:
                skill_exists = exists().where(
                    VacancySkillLink.vacancy_id == VacancyModel.id,
                    VacancySkillLink.skill_id.in_(filters.skill_ids),
                )
                stmt = stmt.where(skill_exists)
            if filters.country_id:
                stmt = stmt.where(VacancyModel.country_id == filters.country_id)
            if filters.city_id:
                stmt = stmt.where(VacancyModel.city_id == filters.city_id)

        count_stmt = select(func.count()).select_from(
            stmt.order_by(None).subquery()
        )
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.order_by(VacancyModel.created_at.desc())

        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)

        if user_id:
            is_saved_subquery = exists().where(
                SavedVacancyModel.vacancy_id == VacancyModel.id,
                SavedVacancyModel.user_id == user_id,
            )
            has_applied_subquery = exists().where(
                ApplicationModel.vacancy_id == VacancyModel.id,
                ApplicationModel.applicant_id == user_id,
            )
            stmt = stmt.add_columns(
                is_saved_subquery.label("is_saved"),
                has_applied_subquery.label("has_applied"),
            )

            try:
                res = await session.execute(stmt)
            except Exception as e:
                logger.error(f"[VacanciesRepository] get_many: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Something went wrong while retrieving vacancies",
                )

            vacancies: list[VacancyModel] = []
            for vacancy, is_saved, has_applied in res.unique().all():
                vacancy.is_saved = is_saved
                vacancy.has_applied = has_applied
                vacancies.append(vacancy)

            data = cast(list[VacancySummary], vacancies)
            return PaginatedResponse(data=data, total=total)

        try:
            res = await session.scalars(stmt)
        except Exception as e:
            logger.error(f"[VacanciesRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving vacancies",
            )

        data = cast(list[VacancySummary], list(res.unique().all()))
        return PaginatedResponse(data=data, total=total)

    @staticmethod
    async def get(
        session: AsyncSession, id: UUID, user_id: UUID | None = None
    ) -> VacancyModel:
        load_options = [
            selectinload(VacancyModel.country),
            selectinload(VacancyModel.city),
            selectinload(VacancyModel.company).selectinload(
                CompanyModel.country
            ),
            selectinload(VacancyModel.company).selectinload(CompanyModel.city),
            selectinload(VacancyModel.skill_links).selectinload(
                VacancySkillLink.skill
            ),
        ]

        if user_id:
            is_saved_subquery = exists().where(
                SavedVacancyModel.vacancy_id == id,
                SavedVacancyModel.user_id == user_id,
            )
            has_applied_subquery = exists().where(
                ApplicationModel.vacancy_id == id,
                ApplicationModel.applicant_id == user_id,
            )

            stmt = (
                select(
                    VacancyModel,
                    is_saved_subquery.label("is_saved"),
                    has_applied_subquery.label("has_applied"),
                )
                .options(*load_options)
                .where(VacancyModel.id == id)
                .execution_options(populate_existing=True)
            )
            row = (await session.execute(stmt)).one_or_none()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vacancy not found",
                )
            vacancy, is_saved, has_applied = row._tuple()
            vacancy.is_saved = is_saved
            vacancy.has_applied = has_applied
        else:
            stmt = (
                select(VacancyModel)
                .options(*load_options)
                .where(VacancyModel.id == id)
                .execution_options(populate_existing=True)
            )
            vacancy = await session.scalar(stmt)
            if not vacancy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vacancy not found",
                )

        if user_id is not None:
            perm_stmt = select(CompanyMemberModel.id).where(
                CompanyMemberModel.user_id == user_id,
                CompanyMemberModel.company_id == vacancy.company_id,
                CompanyMemberModel.role.in_(
                    (CompanyMemberRole.owner, CompanyMemberRole.recruiter)
                ),
            )
            can_manage = await session.scalar(perm_stmt) is not None
        else:
            can_manage = False

        vacancy.permission = PermissionSchema(is_owner=can_manage)
        return vacancy

    @staticmethod
    async def get_optional(
        session: AsyncSession, id: UUID, user_id: UUID | None = None
    ) -> VacancyModel | None:
        load_options = [
            selectinload(VacancyModel.country),
            selectinload(VacancyModel.city),
            selectinload(VacancyModel.company).selectinload(
                CompanyModel.country
            ),
            selectinload(VacancyModel.company).selectinload(CompanyModel.city),
            selectinload(VacancyModel.skill_links).selectinload(
                VacancySkillLink.skill
            ),
        ]

        if user_id:
            is_saved_subquery = exists().where(
                SavedVacancyModel.vacancy_id == id,
                SavedVacancyModel.user_id == user_id,
            )
            has_applied_subquery = exists().where(
                ApplicationModel.vacancy_id == id,
                ApplicationModel.applicant_id == user_id,
            )

            stmt = (
                select(
                    VacancyModel,
                    is_saved_subquery.label("is_saved"),
                    has_applied_subquery.label("has_applied"),
                )
                .options(*load_options)
                .where(VacancyModel.id == id)
                .execution_options(populate_existing=True)
            )
            row = (await session.execute(stmt)).one_or_none()
            if not row:
                return None
            vacancy, is_saved, has_applied = row._tuple()
            vacancy.is_saved = is_saved
            vacancy.has_applied = has_applied
        else:
            stmt = (
                select(VacancyModel)
                .options(*load_options)
                .where(VacancyModel.id == id)
                .execution_options(populate_existing=True)
            )
            vacancy = await session.scalar(stmt)
            if not vacancy:
                return None

        if user_id is not None:
            perm_stmt = select(CompanyMemberModel.id).where(
                CompanyMemberModel.user_id == user_id,
                CompanyMemberModel.company_id == vacancy.company_id,
                CompanyMemberModel.role.in_(
                    (CompanyMemberRole.owner, CompanyMemberRole.recruiter)
                ),
            )
            can_manage = await session.scalar(perm_stmt) is not None
        else:
            can_manage = False

        vacancy.permission = PermissionSchema(is_owner=can_manage)
        return vacancy

    @staticmethod
    async def _replace_skills(
        session: AsyncSession, vacancy_id: UUID, skills: list[dict]
    ):
        await session.execute(
            delete(VacancySkillLink).where(
                VacancySkillLink.vacancy_id == vacancy_id
            )
        )

        for skill in skills:
            session.add(VacancySkillLink(vacancy_id=vacancy_id, **skill))

    @staticmethod
    async def get_skill_link_by_id(
        session: AsyncSession, vacancy_id: UUID, link_id: UUID
    ):
        stmt = (
            select(VacancySkillLink)
            .options(selectinload(VacancySkillLink.skill))
            .where(
                VacancySkillLink.id == link_id,
                VacancySkillLink.vacancy_id == vacancy_id,
            )
        )
        record = await session.scalar(stmt)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vacancy skill link not found",
            )
        return record

    @staticmethod
    async def save_vacancy(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID
    ):
        await VacanciesRepository.get(session, vacancy_id)

        try:
            record = SavedVacancyModel(user_id=user_id, vacancy_id=vacancy_id)
            session.add(record)
            await session.flush()
            return record
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] save_vacancy integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vacancy already saved",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] save_vacancy: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while saving vacancy",
            )

    @staticmethod
    async def unsave_vacancy(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID
    ):
        try:
            stmt = (
                delete(SavedVacancyModel)
                .where(
                    SavedVacancyModel.user_id == user_id,
                    SavedVacancyModel.vacancy_id == vacancy_id,
                )
                .returning(SavedVacancyModel.id)
            )
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Saved vacancy not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] unsave_vacancy: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while unsaving vacancy",
            )

    @staticmethod
    async def get_stats(session: AsyncSession):
        totals_stmt = select(
            func.count(VacancyModel.id).label("total"),
            func.count(VacancyModel.id)
            .filter(VacancyModel.status == VacancyStatus.open)
            .label("open"),
        )
        total, open = (await session.execute(totals_stmt)).one()

        by_status_stmt = (
            select(
                VacancyModel.status, func.count(VacancyModel.id).label("count")
            )
            .group_by(VacancyModel.status)
            .order_by(VacancyModel.status)
        )
        by_status_rows = (await session.execute(by_status_stmt)).all()
        by_status = [
            VacancyStatusBucket(
                key=status, count=count, percentage=percentage(count, total)
            )
            for status, count in by_status_rows
        ]

        by_specialization_stmt = (
            select(
                VacancyModel.specialization,
                func.count(VacancyModel.id).label("count"),
            )
            .group_by(VacancyModel.specialization)
            .order_by(
                func.count(VacancyModel.id).desc(), VacancyModel.specialization
            )
        )
        by_specialization_rows = (
            await session.execute(by_specialization_stmt)
        ).all()
        by_specialization = [
            SpecializationBucket(
                key=specialization,
                count=count,
                percentage=percentage(count, total),
            )
            for specialization, count in by_specialization_rows
        ]

        return VacanciesStatsResponse(
            total=total,
            open=open,
            by_status=by_status,
            by_specialization=by_specialization,
        )
