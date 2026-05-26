from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.companies.models import CompanyModel
from src.apps.companies.repositories.company import CompaniesRepository
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.apps.shared.schemas.enums import (
    ApplicationStatus,
    CompanyMemberRole,
    VacancyStatus,
)
from src.apps.stats.schemas import (
    SpecializationBucket,
    VacanciesStats,
    VacancyStatusBucket,
)
from src.apps.users.models import ResumeModel, UserModel
from src.apps.vacancies.models import (
    ApplicationModel,
    SavedVacancyModel,
    VacancyModel,
    VacancySkillLink,
)
from src.apps.vacancies.schemas.application import (
    ApplicationDetail,
    applicationListDep,
)
from src.apps.vacancies.schemas.vacancy import VacancySummary, vacancyListDep
from src.core.helpers import percentage
from src.core.logger import logger


class VacanciesRepository:
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
            if filters.company_id:
                stmt = stmt.where(VacancyModel.company_id == filters.company_id)
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
                    VacancyModel.specialization == filters.specialization
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

        # Count total BEFORE pagination (filters already applied above)
        # Sorting rows is computationally expensive for the database.
        # If you just want to know how many rows exist, sorting them first is a massive waste of time.
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
    async def get_by_id(
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
            # Correlated subqueries for the specific vacancy — these are cheap single-row lookups.
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
            # row: Row[Tuple[VacancyModel, bool, bool]]
            row = (await session.execute(stmt)).one_or_none()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vacancy not found",
                )
            vacancy, is_saved, has_applied = row._tuple()
            vacancy.is_saved = is_saved
            vacancy.has_applied = has_applied
            return vacancy

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
        return vacancy

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
            return await VacanciesRepository.get_by_id(session, vacancy.id)
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
        vacancy = await VacanciesRepository.get_by_id(session, vacancy_id)
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
            return await VacanciesRepository.get_by_id(session, vacancy_id)
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
        vacancy = await VacanciesRepository.get_by_id(session, vacancy_id)
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
    async def create_skill_link(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID, values: dict
    ):
        vacancy = await VacanciesRepository.get_by_id(session, vacancy_id)
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
            logger.error(
                f"[VacanciesRepository] create_skill_link integrity: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vacancy skill already exists or references invalid skill",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] create_skill_link: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating vacancy skill",
            )

    @staticmethod
    async def update_skill_link(
        session: AsyncSession,
        user_id: UUID,
        vacancy_id: UUID,
        link_id: UUID,
        values: dict,
    ):
        vacancy = await VacanciesRepository.get_by_id(session, vacancy_id)
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
            logger.error(
                f"[VacanciesRepository] update_skill_link integrity: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vacancy skill data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] update_skill_link: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating vacancy skill",
            )

    @staticmethod
    async def delete_skill_link(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID, link_id: UUID
    ):
        vacancy = await VacanciesRepository.get_by_id(session, vacancy_id)
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
            logger.error(f"[VacanciesRepository] delete_skill_link: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting vacancy skill",
            )

    @staticmethod
    async def get_applications(
        session: AsyncSession,
        pagination: paginationDep,
        filters: applicationListDep,
    ) -> PaginatedResponse[ApplicationDetail]:
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

        # Count total before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        # Apply loading options and ordering
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
        data = cast(list[ApplicationDetail], list(res.all()))
        return PaginatedResponse(data=data, total=total)

    @staticmethod
    async def get_application_by_id(
        session: AsyncSession, id: UUID
    ) -> ApplicationModel:
        stmt = (
            select(ApplicationModel)
            .options(
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
            )
            .where(ApplicationModel.id == id)
            .execution_options(populate_existing=True)
        )
        record = await session.scalar(stmt)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        return record

    @staticmethod
    async def apply_to_vacancy(
        session: AsyncSession, applicant_id: UUID, data: dict
    ) -> ApplicationModel:
        vacancy = await VacanciesRepository.get_by_id(
            session, data["vacancy_id"]
        )
        if vacancy.status != VacancyStatus.open:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vacancy is not open for applications",
            )

        resume_id = data.get("resume_id")
        if resume_id:
            resume_stmt = select(ResumeModel.id).where(
                ResumeModel.id == resume_id, ResumeModel.user_id == applicant_id
            )
            resume_exists = await session.scalar(resume_stmt)
            if not resume_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resume not found",
                )

        try:
            application = ApplicationModel(applicant_id=applicant_id, **data)
            session.add(application)
            await session.flush()
            return await VacanciesRepository.get_application_by_id(
                session, application.id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(
                f"[VacanciesRepository] apply_to_vacancy integrity: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already exists or references invalid data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[VacanciesRepository] apply_to_vacancy: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while applying to vacancy",
            )

    @staticmethod
    async def update_application_status(
        session: AsyncSession,
        application_id: UUID,
        application_status: ApplicationStatus,
        recruiter_note: str | None = None,
        user_id: UUID | None = None,
    ) -> ApplicationModel | None:
        application = await VacanciesRepository.get_application_by_id(
            session, application_id
        )
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
            return await VacanciesRepository.get_application_by_id(
                session, application_id
            )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(
                f"[VacanciesRepository] update_application_status: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating application",
            )

    @staticmethod
    async def save_vacancy(
        session: AsyncSession, user_id: UUID, vacancy_id: UUID
    ):
        await VacanciesRepository.get_by_id(session, vacancy_id)

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
        # by_status_rows: Sequence[Row[Tuple[VacancyStatus, int]]]
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
        # by_specialization_rows: Sequence[Row[Tuple[Specialization, int]]]
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

        return VacanciesStats(
            total=total,
            open=open,
            by_status=by_status,
            by_specialization=by_specialization,
        )
