from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.companies.models import CompanyModel
from src.apps.stats.schemas import CompaniesStats, CompanyTypeBucket
from src.core.helpers import percentage


class CompaniesRepository:
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
