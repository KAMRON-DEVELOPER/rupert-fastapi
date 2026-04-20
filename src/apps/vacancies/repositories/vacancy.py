from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.shared.enums import ApplicationStatus, VacancyStatus
from src.apps.shared.schemas import Pagination
from src.apps.stats.schemas import SpecializationBucket, VacanciesStats, VacancyStatusBucket
from src.apps.vacancies.models import ApplicationModel, SavedVacancyModel, VacancyModel, VacancySkillLink
from src.apps.vacancies.schemas import ApplicationFilters, VacancyFilters
from src.core.helpers import percentage


class VacanciesRepository:
    @staticmethod
    async def get_many(
        session: AsyncSession,
        user_id: UUID | None = None,
        pagination: Pagination | None = None,
        filters: VacancyFilters | None = None,
    ) -> list[VacancyModel]:
        stmt = select(VacancyModel).options(selectinload(VacancyModel.company)).order_by(VacancyModel.created_at.desc())

        if pagination:
            stmt.offset(pagination.offset).limit(pagination.limit)

        if user_id:
            is_saved_subquery = exists().where(SavedVacancyModel.vacancy_id == VacancyModel.id, SavedVacancyModel.user_id == user_id)
            has_applied_subquery = exists().where(ApplicationModel.vacancy_id == VacancyModel.id, ApplicationModel.applicant_id == user_id)
            stmt = stmt.add_columns(is_saved_subquery.label("is_saved"), has_applied_subquery.label("has_applied"))

        if filters:
            if filters.company_id:
                stmt = stmt.where(VacancyModel.company_id == filters.company_id)
            if filters.title:
                stmt = stmt.where(VacancyModel.title.ilike(f"%{filters.title}%"))
            if filters.submission_type:
                stmt = stmt.where(VacancyModel.submission_type == filters.submission_type)
            if filters.specialization:
                stmt = stmt.where(VacancyModel.specialization == filters.specialization)
            if filters.salary_min is not None:
                stmt = stmt.where(VacancyModel.salary_max >= filters.salary_min)
            if filters.salary_max is not None:
                stmt = stmt.where(VacancyModel.salary_min <= filters.salary_max)
            if filters.salary_currency:
                stmt = stmt.where(VacancyModel.salary_currency == filters.salary_currency)
            if filters.years_of_experience_min is not None:
                stmt = stmt.where(VacancyModel.years_of_experience_min >= filters.years_of_experience_min)
            if filters.work_format:
                stmt = stmt.where(VacancyModel.work_format == filters.work_format)
            if filters.employment_type:
                stmt = stmt.where(VacancyModel.employment_type == filters.employment_type)
            if filters.skill_ids:
                stmt = stmt.join(VacancyModel.skill_links).where(VacancySkillLink.skill_id.in_(filters.skill_ids))

        if user_id:
            res = await session.execute(stmt)
            vacancies = []
            for row in res.unique().all():
                vacancy = row[0]
                vacancy.is_saved = row[1]
                vacancy.has_applied = row[2]
                vacancies.append(vacancy)
            return vacancies

        res = await session.scalars(stmt)
        return list(res.unique().all())

    @staticmethod
    async def get_applications(
        session: AsyncSession,
        pagination: Pagination | None = None,
        filters: ApplicationFilters | None = None,
    ) -> list[ApplicationModel]:
        stmt = (
            select(ApplicationModel)
            .options(
                selectinload(ApplicationModel.vacancy).selectinload(VacancyModel.company),
                selectinload(ApplicationModel.resume),
                selectinload(ApplicationModel.applicant),
            )
            .order_by(ApplicationModel.created_at.desc())
        )

        if pagination:
            stmt.offset(pagination.offset).limit(pagination.limit)

        if filters:
            if filters.vacancy_id:
                stmt = stmt.where(ApplicationModel.vacancy_id == filters.vacancy_id)
            if filters.applicant_id:
                stmt = stmt.where(ApplicationModel.applicant_id == filters.applicant_id)
            if filters.status:
                stmt = stmt.where(ApplicationModel.status == filters.status)

        res = await session.scalars(stmt)
        return list(res.all())

    @staticmethod
    async def get_by_id(session: AsyncSession, vacancy_id: UUID) -> VacancyModel | None:
        stmt = (
            select(VacancyModel)
            .options(
                selectinload(VacancyModel.company),
                selectinload(VacancyModel.skill_links).selectinload(VacancySkillLink.skill),
            )
            .where(VacancyModel.id == vacancy_id)
        )
        return await session.scalar(stmt)

    @staticmethod
    async def create(session: AsyncSession, company_id: UUID, data: dict) -> VacancyModel:
        skills_data = data.pop("skills", [])
        vacancy = VacancyModel(company_id=company_id, **data)
        session.add(vacancy)
        await session.flush()

        for skill_item in skills_data:
            link = VacancySkillLink(vacancy_id=vacancy.id, **skill_item)
            session.add(link)

        await session.commit()
        await session.refresh(vacancy)
        return vacancy

    @staticmethod
    async def update(session: AsyncSession, vacancy_id: UUID, data: dict) -> VacancyModel | None:
        vacancy = await VacanciesRepository.get_by_id(session, vacancy_id)
        if not vacancy:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(vacancy, key, value)

        await session.commit()
        await session.refresh(vacancy)
        return vacancy

    @staticmethod
    async def delete(session: AsyncSession, vacancy_id: UUID) -> bool:
        vacancy = await VacanciesRepository.get_by_id(session, vacancy_id)
        if not vacancy:
            return False

        await session.delete(vacancy)
        await session.commit()
        return True

    @staticmethod
    async def get_application_by_id(session: AsyncSession, application_id: UUID) -> ApplicationModel | None:
        stmt = (
            select(ApplicationModel)
            .options(
                selectinload(ApplicationModel.vacancy).selectinload(VacancyModel.company),
                selectinload(ApplicationModel.resume),
                selectinload(ApplicationModel.applicant),
            )
            .where(ApplicationModel.id == application_id)
        )
        return await session.scalar(stmt)

    @staticmethod
    async def apply_to_vacancy(session: AsyncSession, applicant_id: UUID, data: dict) -> ApplicationModel:
        application = ApplicationModel(applicant_id=applicant_id, **data)
        session.add(application)
        await session.commit()
        await session.refresh(application)
        return application

    @staticmethod
    async def update_application_status(session: AsyncSession, application_id: UUID, status: ApplicationStatus, recruiter_note: str | None = None) -> ApplicationModel | None:
        application = await VacanciesRepository.get_application_by_id(session, application_id)
        if not application:
            return None

        application.status = status
        if recruiter_note is not None:
            application.recruiter_note = recruiter_note

        await session.commit()
        await session.refresh(application)
        return application

    @staticmethod
    async def get_stats(session: AsyncSession):
        totals_stmt = select(
            func.count(VacancyModel.id).label("total"),
            func.count(VacancyModel.id).filter(VacancyModel.status == VacancyStatus.open).label("open"),
        )
        total, open = (await session.execute(totals_stmt)).one()

        by_status_stmt = (
            select(
                VacancyModel.status,
                func.count(VacancyModel.id).label("count"),
            )
            .group_by(VacancyModel.status)
            .order_by(VacancyModel.status)
        )
        # by_status_rows: Sequence[Row[Tuple[VacancyStatus, int]]]
        by_status_rows = (await session.execute(by_status_stmt)).all()
        by_status = [
            VacancyStatusBucket(
                key=status,
                count=count,
                percentage=percentage(count, total),
            )
            for status, count in by_status_rows
        ]

        by_specialization_stmt = (
            select(
                VacancyModel.specialization,
                func.count(VacancyModel.id).label("count"),
            )
            .group_by(VacancyModel.specialization)
            .order_by(func.count(VacancyModel.id).desc(), VacancyModel.specialization)
        )
        # by_specialization_rows: Sequence[Row[Tuple[Specialization, int]]]
        by_specialization_rows = (await session.execute(by_specialization_stmt)).all()
        by_specialization = [
            SpecializationBucket(
                key=specialization,
                count=count,
                percentage=percentage(count, total),
            )
            for specialization, count in by_specialization_rows
        ]

        return VacanciesStats(total=total, open=open, by_status=by_status, by_specialization=by_specialization)
