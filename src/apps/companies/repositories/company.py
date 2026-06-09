from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.companies.models import CompanyMemberModel, CompanyModel
from src.apps.companies.schemas.company import (
    CompanyDetail,
    CompanySummary,
    companyListDep,
)
from src.apps.shared.schemas import PaginatedResponse, paginationDep
from src.apps.shared.schemas.enums import CompanyMemberRole, VacancyStatus
from src.apps.stats.schemas import CompaniesStatsResponse, CompanyTypeBucket
from src.apps.vacancies.models import VacancyModel, VacancySkillLink
from src.core.helpers import percentage
from src.core.logger import logger


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
                VacancyModel.status == VacancyStatus.open,
            )
            .correlate(CompanyModel)
            .scalar_subquery()
            .label("open_vacancies_count")
        )

        stmt = (
            select(CompanyModel, open_vacancies_count)
            .options(
                selectinload(CompanyModel.country),
                selectinload(CompanyModel.city),
            )
            .execution_options(populate_existing=True)
        )

        if filters:
            if filters.name:
                stmt = stmt.where(CompanyModel.name.like(f"%{filters.name}%"))
            if filters.type:
                stmt = stmt.where(CompanyModel.type == filters.type)
            if filters.status:
                stmt = stmt.where(CompanyModel.status == filters.status)
            if filters.country_id:
                stmt = stmt.where(CompanyModel.country_id == filters.country_id)
            if filters.city_id:
                stmt = stmt.where(CompanyModel.city_id == filters.city_id)
            if filters.has_open_vacancies is not None:
                open_vacancy_exists = exists().where(
                    VacancyModel.company_id == CompanyModel.id,
                    VacancyModel.status == VacancyStatus.open,
                )
                if filters.has_open_vacancies:
                    stmt = stmt.where(open_vacancy_exists)
                else:
                    stmt = stmt.where(~open_vacancy_exists)
            if filters.skill_ids:
                skill_exists = exists().where(
                    VacancyModel.company_id == CompanyModel.id,
                    VacancySkillLink.vacancy_id == VacancyModel.id,
                    VacancySkillLink.skill_id.in_(filters.skill_ids),
                )
                stmt = stmt.where(skill_exists)

        count_stmt = select(func.count()).select_from(
            stmt.order_by(None).subquery()
        )
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.order_by(CompanyModel.created_at.desc())

        if pagination:
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)

        # res: Sequence[Tuple[CompanyModel, int]]
        try:
            res = (await session.execute(stmt)).tuples().all()
        except Exception as e:
            logger.error(f"[CompaniesRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving companies",
            )

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
                VacancyModel.status == VacancyStatus.open,
            )
            .correlate(CompanyModel)
            .scalar_subquery()
            .label("open_vacancies_count")
        )

        member_count = (
            select(func.count(CompanyMemberModel.id))
            .where(CompanyMemberModel.company_id == CompanyModel.id)
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
                selectinload(CompanyModel.country),
                selectinload(CompanyModel.city),
            )
            .where(CompanyModel.id == company_id)
            .execution_options(populate_existing=True)
        )

        try:
            res = (await session.execute(stmt)).one_or_none()
        except Exception as e:
            logger.error(f"[CompaniesRepository] get_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving company",
            )

        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

        company, open_count, member_count_value = res._tuple()
        company.open_vacancies_count = open_count
        company.member_count = member_count_value
        return cast(CompanyDetail, company)

    @staticmethod
    async def create(session: AsyncSession, user_id: UUID, values: dict):
        record = CompanyModel(**values)

        try:
            session.add(record)
            await session.flush()
            session.add(
                CompanyMemberModel(
                    user_id=user_id,
                    company_id=record.id,
                    role=CompanyMemberRole.owner,
                )
            )
            await session.flush()
            return await CompaniesRepository.get_by_id(session, record.id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company already exists or contains invalid data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating company",
            )

    @staticmethod
    async def update(
        session: AsyncSession, user_id: UUID, company_id: UUID, values: dict
    ):
        await CompaniesRepository.ensure_member(
            session, user_id, company_id, (CompanyMemberRole.owner,)
        )

        try:
            if values:
                stmt = (
                    update(CompanyModel)
                    .where(CompanyModel.id == company_id)
                    .values(values)
                    .returning(CompanyModel.id)
                )
                await session.scalar(stmt)
                await session.flush()

            return await CompaniesRepository.get_by_id(session, company_id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company already exists or contains invalid data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating company",
            )

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, company_id: UUID):
        await CompaniesRepository.ensure_member(
            session, user_id, company_id, (CompanyMemberRole.owner,)
        )

        stmt = (
            delete(CompanyModel)
            .where(CompanyModel.id == company_id)
            .returning(CompanyModel.id)
        )

        try:
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting company",
            )

    @staticmethod
    async def ensure_member(
        session: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        roles: tuple[CompanyMemberRole, ...] | None = None,
    ):
        stmt = select(CompanyMemberModel).where(
            CompanyMemberModel.user_id == user_id,
            CompanyMemberModel.company_id == company_id,
        )
        member = await session.scalar(stmt)

        if not member:
            exists_stmt = select(CompanyModel.id).where(
                CompanyModel.id == company_id
            )
            company_exists = await session.scalar(exists_stmt)
            if not company_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this company",
            )

        if roles and member.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this company",
            )

        return member

    @staticmethod
    async def add_member(
        session: AsyncSession, user_id: UUID, company_id: UUID, values: dict
    ):
        await CompaniesRepository.ensure_member(
            session, user_id, company_id, (CompanyMemberRole.owner,)
        )

        try:
            record = CompanyMemberModel(company_id=company_id, **values)
            session.add(record)
            await session.flush()
            return await CompaniesRepository.get_member_by_id(
                session, company_id, record.id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] add_member integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company member already exists or references invalid user",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] add_member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while adding company member",
            )

    @staticmethod
    async def get_member_by_id(
        session: AsyncSession, company_id: UUID, member_id: UUID
    ):
        stmt = (
            select(CompanyMemberModel)
            .options(selectinload(CompanyMemberModel.user))
            .where(
                CompanyMemberModel.id == member_id,
                CompanyMemberModel.company_id == company_id,
            )
        )
        record = await session.scalar(stmt)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company member not found",
            )
        return record

    @staticmethod
    async def update_member(
        session: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        member_id: UUID,
        values: dict,
    ):
        await CompaniesRepository.ensure_member(
            session, user_id, company_id, (CompanyMemberRole.owner,)
        )
        member = await CompaniesRepository.get_member_by_id(
            session, company_id, member_id
        )

        if (
            member.user_id == user_id
            and values.get("role") != CompanyMemberRole.owner
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company owner cannot change own role",
            )

        try:
            if values:
                stmt = (
                    update(CompanyMemberModel)
                    .where(
                        CompanyMemberModel.id == member_id,
                        CompanyMemberModel.company_id == company_id,
                    )
                    .values(values)
                    .returning(CompanyMemberModel.id)
                )
                await session.scalar(stmt)
                await session.flush()

            return await CompaniesRepository.get_member_by_id(
                session, company_id, member_id
            )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] update_member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating company member",
            )

    @staticmethod
    async def delete_member(
        session: AsyncSession, user_id: UUID, company_id: UUID, member_id: UUID
    ):
        await CompaniesRepository.ensure_member(
            session, user_id, company_id, (CompanyMemberRole.owner,)
        )
        member = await CompaniesRepository.get_member_by_id(
            session, company_id, member_id
        )

        if member.user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company owner cannot remove self",
            )

        try:
            stmt = (
                delete(CompanyMemberModel)
                .where(
                    CompanyMemberModel.id == member_id,
                    CompanyMemberModel.company_id == company_id,
                )
                .returning(CompanyMemberModel.id)
            )
            await session.scalar(stmt)
            await session.flush()
        except Exception as e:
            await session.rollback()
            logger.error(f"[CompaniesRepository] delete_member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting company member",
            )

    @staticmethod
    async def get_stats(session: AsyncSession):
        total = await session.scalar(select(func.count(CompanyModel.id))) or 0

        by_type_stmt = (
            select(
                CompanyModel.type, func.count(CompanyModel.id).label("count")
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

        return CompaniesStatsResponse(total=total, by_type=by_type)
