from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.enums import VacancyStatus
from src.apps.stats.schemas import SpecializationBucket, VacanciesStats, VacancyStatusBucket
from src.apps.vacancies.models import VacancyModel
from src.apps.vacancies.schemas import VacancyCardOut
from src.core.helpers import percentage


class VacanciesRepository:
    @staticmethod
    async def get_many(offset: int, limit: int, session: AsyncSession) -> list[VacancyCardOut]:
        stmt = select(VacancyModel.company, VacancyModel.title).offset(offset).limit(limit)
        res = (await session.scalars(stmt)).all()

        return VacancyCardOut()

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
