from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.enums import JobSearchStatus
from src.apps.stats.schemas import DailyActiveUsersBucket, JobSearchStatusBucket, SpecializationBucket, UsersStats
from src.apps.users.models import ActivityModel, UserModel
from src.apps.users.schemas import UserUpdateIn
from src.core.helpers import percentage


class UsersRepository:
    @staticmethod
    async def find_by_email(email: str, session: AsyncSession):
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(email: str, password_hash: str | None, first_name: str, last_name: str, session: AsyncSession):
        record = UserModel(email=email, password_hash=password_hash, first_name=first_name, last_name=last_name)
        session.add(record)
        await session.flush()
        return record

    @staticmethod
    async def get_by_id(id: UUID, session: AsyncSession):
        stmt = select(UserModel).where(UserModel.id == id)
        result = await session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def update_by_id(id: UUID, schm: UserUpdateIn, session: AsyncSession):
        stmt = update(UserModel).where(UserModel.id == id).values(schm.model_dump(exclude_unset=True)).returning(UserModel)
        result = await session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def delete_by_id(id: UUID, session: AsyncSession):
        stmt = delete(UserModel).where(UserModel.id == id)
        await session.execute(stmt)

    @staticmethod
    async def set_email_verified(id: UUID, session: AsyncSession):
        stmt = update(UserModel).where(UserModel.id == id).values(email_verified=True)
        await session.execute(stmt)

    @staticmethod
    async def get_stats(session: AsyncSession):
        now = datetime.now(UTC)
        today = now.date()
        start_date = today - timedelta(days=29)

        looking_statuses = (JobSearchStatus.actively_looking, JobSearchStatus.open_to_offers, JobSearchStatus.interviewing)

        totals_stmt = select(
            func.count(UserModel.id).label("total"),
            func.count(UserModel.id).filter(UserModel.job_search_status.in_(looking_statuses)).label("looking_for_job_count"),
        )
        # row: Row[Tuple[int, int]]
        row = (await session.execute(totals_stmt)).one()
        total, looking_for_job_count = row
        looking_for_job_percentage = percentage(looking_for_job_count, total)

        # dau_chart_rows: Sequence[Tuple[date, int]]
        dau_chart_rows = (
            (
                await session.execute(
                    select(
                        ActivityModel.activity_date,
                        func.count(ActivityModel.user_id).label("count"),
                    )
                    .where(ActivityModel.activity_date >= start_date)
                    .group_by(ActivityModel.activity_date)
                    .order_by(ActivityModel.activity_date)
                )
            )
            .tuples()
            .all()
        )
        dau_counts_by_date = {activity_date: count for activity_date, count in dau_chart_rows}
        dau_chart = [
            DailyActiveUsersBucket(
                count=dau_counts_by_date.get(day, 0),
                date=day,
            )
            for offset in range(30)
            for day in [start_date + timedelta(days=offset)]
        ]

        by_status_stmt = (
            select(
                UserModel.job_search_status,
                func.count(UserModel.id).label("count"),
            )
            .group_by(UserModel.job_search_status)
            .order_by(UserModel.job_search_status)
        )
        # by_status_rows: Sequence[Row[Tuple[JobSearchStatus, int]]]
        by_status_rows = (await session.execute(by_status_stmt)).all()
        by_job_search_status = [
            JobSearchStatusBucket(
                key=status,
                count=count,
                percentage=percentage(count, total),
            )
            for status, count in by_status_rows
        ]

        by_specialization_stmt = (
            select(
                UserModel.specialization,
                func.count(UserModel.id).label("count"),
            )
            .where(UserModel.specialization.is_not(None))
            .group_by(UserModel.specialization)
            .order_by(func.count(UserModel.id).desc(), UserModel.specialization)
        )
        # by_specialization_rows: Sequence[Row[Tuple[Specialization | None, int]]]
        by_specialization_rows = (await session.execute(by_specialization_stmt)).all()
        by_specialization = [
            SpecializationBucket(
                key=specialization,
                count=count,
                percentage=percentage(count, total),
            )
            for specialization, count in by_specialization_rows
        ]

        return UsersStats(
            total=total,
            looking_for_job_count=looking_for_job_count,
            looking_for_job_percentage=looking_for_job_percentage,
            dau_chart=dau_chart,
            by_job_search_status=by_job_search_status,
            by_specialization=by_specialization,
        )
