from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.chats.schemas.chat_participant import ChatListUserResponse
from src.apps.shared.schemas import PaginatedResponse
from src.apps.shared.schemas.enums import JobSearchStatus
from src.apps.stats.schemas import (
    DailyActiveUsersBucket,
    JobSearchStatusBucket,
    SpecializationBucket,
    UsersStats,
)
from src.apps.users.models import (
    ActivityModel,
    ResumeModel,
    UserModel,
    UserSkillLink,
)
from src.core.helpers import percentage
from src.core.logger import logger


class UsersRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str | None = None,
        email_verified=False,
    ):
        record = UserModel(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            email_verified=email_verified,
        )

        try:
            session.add(record)
            await session.flush()
            return record
        except Exception as e:
            await session.rollback()
            logger.error(f"[UsersRepository] create: {e}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating user",
            )

    @staticmethod
    async def update(session: AsyncSession, id: UUID, values: dict):
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values(values)
            .returning(UserModel.id)
        )

        try:
            updated_id = await session.scalar(stmt)

            if not updated_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found to update",
                )

            await session.flush()
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[UsersRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating user",
            )

    @staticmethod
    async def delete(session: AsyncSession, id: UUID):
        stmt = (
            delete(UserModel).where(UserModel.id == id).returning(UserModel.id)
        )

        try:
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[UsersRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting user",
            )

    @staticmethod
    async def set_email_verified(session: AsyncSession, id: UUID):
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values(email_verified=True)
            .returning(UserModel.id)
        )

        try:
            updated_id = await session.scalar(stmt)

            if not updated_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found to set email verified",
                )

            await session.flush()
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[UsersRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while setting email verified",
            )

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str, required=True):
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.country), selectinload(UserModel.city)
            )
            .where(UserModel.email == email)
        )

        try:
            record = await session.scalar(stmt)

            if not record and required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found associated with the email",
                )

            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[UsersRepository] get_by_email: {e}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user by email",
            )

    @staticmethod
    async def get_summary(session: AsyncSession, id: UUID, required=True):
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.country), selectinload(UserModel.city)
            )
            .where(UserModel.id == id)
        )

        try:
            record = await session.scalar(stmt)

            if not record and required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found",
                )

            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[UsersRepository] get_summary_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user summary by id",
            )

    @staticmethod
    async def get_detail(session: AsyncSession, id: UUID, required=True):
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.country),
                selectinload(UserModel.city),
                selectinload(UserModel.resumes).selectinload(
                    ResumeModel.country
                ),
                selectinload(UserModel.resumes).selectinload(ResumeModel.city),
                selectinload(UserModel.skill_links).selectinload(
                    UserSkillLink.skill
                ),
                selectinload(UserModel.work_experiences),
            )
            .where(UserModel.id == id)
        )

        try:
            record = await session.scalar(stmt)

            if not record and required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found",
                )

            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[UsersRepository] get_detail_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user detail by id",
            )

    @staticmethod
    async def search(
        session: AsyncSession,
        query: str | None,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[ChatListUserResponse]:
        search_pattern = f"%{query}%" if query else "%"

        user_filter = or_(
            UserModel.first_name.ilike(search_pattern),
            UserModel.last_name.ilike(search_pattern),
        )

        data_stmt = (
            select(
                UserModel.id,
                UserModel.first_name,
                UserModel.last_name,
                UserModel.avatar_url,
            )
            .where(user_filter)
            .order_by(UserModel.first_name)
            .offset(offset)
            .limit(limit)
        )

        count_stmt = (
            select(func.count()).select_from(UserModel).where(user_filter)
        )

        try:
            rows = (await session.execute(data_stmt)).all()
            total = await session.scalar(count_stmt) or 0

            return PaginatedResponse(
                data=[
                    ChatListUserResponse(
                        id=row.id,
                        first_name=row.first_name,
                        last_name=row.last_name,
                        avatar_url=row.avatar_url,
                    )
                    for row in rows
                ],
                total=total,
            )
        except Exception as e:
            logger.error(f"[UsersRepository] search: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while searching users",
            )

    @staticmethod
    async def get_stats(session: AsyncSession):
        now = datetime.now(UTC)
        today = now.date()
        start_date = today - timedelta(days=29)

        looking_statuses = (
            JobSearchStatus.actively_looking,
            JobSearchStatus.open_to_offers,
            JobSearchStatus.interviewing,
        )

        totals_stmt = select(
            func.count(UserModel.id).label("total"),
            func.count(UserModel.id)
            .filter(UserModel.job_search_status.in_(looking_statuses))
            .label("looking_for_job_count"),
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
        dau_counts_by_date = {
            activity_date: count for activity_date, count in dau_chart_rows
        }
        dau_chart = [
            DailyActiveUsersBucket(
                count=dau_counts_by_date.get(day, 0), date=day
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
                key=status, count=count, percentage=percentage(count, total)
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

        return UsersStats(
            total=total,
            looking_for_job_count=looking_for_job_count,
            looking_for_job_percentage=looking_for_job_percentage,
            dau_chart=dau_chart,
            by_job_search_status=by_job_search_status,
            by_specialization=by_specialization,
        )
