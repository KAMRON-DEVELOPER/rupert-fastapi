from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.companies.models import CompanyMemberModel, CompanyModel
from src.apps.companies.schemas.company import (
    CompanyDetail,
    CompanySummary,
    companyListDep,
)
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.apps.stats.schemas import CompaniesStats, CompanyTypeBucket
from src.apps.vacancies.models import VacancyModel
from src.core.helpers import percentage


class CompaniesRepository:
    @staticmethod
    async def get_many(
        session: AsyncSession,
        pagination: paginationDep,
        filters: companyListDep | None,
    ) -> PaginatedResponse[CompanySummary]:
        # Correlated scalar subquery: counts open vacancies for each company
        # in the outer query. SQLAlchemy auto-correlates this because CompanyModel.id
        # is referenced from the outer SELECT.
        open_vacancies_count = (
            select(func.count(VacancyModel.id))
            .where(
                VacancyModel.company_id == CompanyModel.id,
            )
            .correlate(CompanyModel)
            .scalar_subquery()
            .label("open_vacancies_count")
        )

        stmt = select(CompanyModel, open_vacancies_count)

        if filters:
            if filters.name:
                stmt = stmt.where(CompanyModel.name.like(f"%{filters.name}%"))
            if filters.type:
                stmt = stmt.where(CompanyModel.type == filters.type)
            if filters.status:
                stmt = stmt.where(CompanyModel.status == filters.status)
            if filters.country:
                stmt = stmt.where(CompanyModel.country == filters.country)
            if filters.city:
                stmt = stmt.where(CompanyModel.city == filters.city)
            if filters.has_open_vacancies:
                pass
            if filters.skill_ids:
                pass

        count_stmt = select(func.count()).select_from(
            stmt.order_by(None).subquery()
        )
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.order_by(CompanyModel.created_at.desc())

        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)

        # res: Sequence[Tuple[CompanyModel, int]]
        res = (await session.execute(stmt)).tuples().all()

        companies: list[CompanyModel] = []
        for company, open_count in res:
            company.open_vacancies_count = open_count
            companies.append(company)

        data = cast(list[CompanySummary], companies)
        return PaginatedResponse(data=data, total=total)

    @staticmethod
    async def get_by_id(
        session: AsyncSession, company_id: UUID
    ) -> CompanyDetail:
        open_vacancies_count = (
            select(func.count(VacancyModel.id))
            .where(
                VacancyModel.company_id == CompanyModel.id,
            )
            .correlate(CompanyModel)
            .scalar_subquery()
            .label("open_vacancies_count")
        )

        member_count = (
            select(func.count(CompanyMemberModel.id))
            .where(
                CompanyMemberModel.company_id == CompanyModel.id,
            )
            .correlate(CompanyModel)
            .scalar_subquery()
            .label("member_count")
        )

        stmt = (
            select(CompanyModel, open_vacancies_count, member_count)
            .options(
                selectinload(CompanyModel.members).selectinload(
                    CompanyMemberModel.user
                ),
                selectinload(CompanyModel.vacancies),
            )
            .where(CompanyModel.id == company_id)
        )

        # res: Tuple[CompanyModel, int, int]
        res = (await session.execute(stmt)).one().tuple()

        company, open_count, member_count_value = res
        company.open_vacancies_count = open_count
        company.member_count = member_count_value
        return cast(CompanyDetail, company)

    @staticmethod
    async def get_stats(session: AsyncSession):
        total = await session.scalar(select(func.count(CompanyModel.id))) or 0

        by_type_stmt = (
            select(
                CompanyModel.type,
                func.count(CompanyModel.id).label("count"),
            )
            .group_by(CompanyModel.type)
            .order_by(CompanyModel.type)
        )
        # by_type_rows: Sequence[Row[Tuple[CompanyType, int]]]
        by_type_rows = (await session.execute(by_type_stmt)).all()
        by_type = [
            CompanyTypeBucket(
                key=company_type,
                count=count,
                percentage=percentage(count, total),
            )
            for company_type, count in by_type_rows
        ]

        return CompaniesStats(total=total, by_type=by_type)
