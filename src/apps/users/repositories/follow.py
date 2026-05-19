from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from src.apps.shared.schemas import PaginatedResponse, PaginationQuery
from src.apps.shared.schemas.enums import FollowPolicy, FollowStatus
from src.apps.users.models import FollowModel, UserModel
from src.apps.users.schemas.follow import FollowResponse
from src.core.logger import logger


class FollowsRepository:
    @staticmethod
    async def follow(
        session: AsyncSession, follower_id: UUID, following_id: UUID
    ):
        if follower_id == following_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot follow yourself",
            )

        try:
            target = await session.scalar(
                select(UserModel).where(UserModel.id == following_id)
            )
            if not target:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            follow_status = (
                FollowStatus.accepted
                if target.follow_policy == FollowPolicy.auto_accept
                else FollowStatus.pending
            )
            record = FollowModel(
                follower_id=follower_id,
                following_id=following_id,
                status=follow_status,
            )
            session.add(record)
            await session.flush()
            return await FollowsRepository.get_by_id(session, record.id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[FollowsRepository] follow integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Follow already exists",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[FollowsRepository] follow: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while following user",
            )

    @staticmethod
    async def get_by_id(session: AsyncSession, follow_id: UUID):
        stmt = (
            select(FollowModel)
            .options(
                selectinload(FollowModel.follower),
                selectinload(FollowModel.following),
            )
            .where(FollowModel.id == follow_id)
        )
        return await session.scalar(stmt)

    @staticmethod
    async def unfollow(
        session: AsyncSession, follower_id: UUID, following_id: UUID
    ):
        stmt = (
            delete(FollowModel)
            .where(
                FollowModel.follower_id == follower_id,
                FollowModel.following_id == following_id,
            )
            .returning(FollowModel.id)
        )
        try:
            deleted_id = await session.scalar(stmt)
            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Follow not found",
                )
            await session.flush()
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[FollowsRepository] unfollow: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while unfollowing user",
            )

    @staticmethod
    async def _paginate(
        session: AsyncSession,
        stmt: Select[tuple[FollowModel]],
        pagination: PaginationQuery,
    ) -> PaginatedResponse[FollowResponse]:
        count_stmt = select(func.count()).select_from(
            stmt.order_by(None).subquery()
        )
        total = await session.scalar(count_stmt) or 0
        records = (
            await session.scalars(
                stmt.offset(pagination.offset).limit(pagination.limit)
            )
        ).all()
        data = [FollowResponse.model_validate(record) for record in records]
        return PaginatedResponse(data=data, total=total)

    @staticmethod
    async def list_followers(
        session: AsyncSession, user_id: UUID, pagination: PaginationQuery
    ) -> PaginatedResponse[FollowResponse]:
        stmt = (
            select(FollowModel)
            .options(
                selectinload(FollowModel.follower),
                selectinload(FollowModel.following),
            )
            .where(
                FollowModel.following_id == user_id,
                FollowModel.status == FollowStatus.accepted,
            )
            .order_by(FollowModel.created_at.desc())
        )
        try:
            return await FollowsRepository._paginate(session, stmt, pagination)
        except Exception as e:
            logger.error(f"[FollowsRepository] list_followers: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving followers",
            )

    @staticmethod
    async def list_following(
        session: AsyncSession, user_id: UUID, pagination: PaginationQuery
    ) -> PaginatedResponse[FollowResponse]:
        stmt = (
            select(FollowModel)
            .options(
                selectinload(FollowModel.follower),
                selectinload(FollowModel.following),
            )
            .where(
                FollowModel.follower_id == user_id,
                FollowModel.status == FollowStatus.accepted,
            )
            .order_by(FollowModel.created_at.desc())
        )
        try:
            return await FollowsRepository._paginate(session, stmt, pagination)
        except Exception as e:
            logger.error(f"[FollowsRepository] list_following: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving following",
            )

    @staticmethod
    async def list_pending_requests(
        session: AsyncSession, user_id: UUID, pagination: PaginationQuery
    ) -> PaginatedResponse[FollowResponse]:
        stmt = (
            select(FollowModel)
            .options(
                selectinload(FollowModel.follower),
                selectinload(FollowModel.following),
            )
            .where(
                FollowModel.following_id == user_id,
                FollowModel.status == FollowStatus.pending,
            )
            .order_by(FollowModel.created_at.desc())
        )
        try:
            return await FollowsRepository._paginate(session, stmt, pagination)
        except Exception as e:
            logger.error(f"[FollowsRepository] list_pending_requests: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving follow requests",
            )

    @staticmethod
    async def update_request_status(
        session: AsyncSession,
        user_id: UUID,
        follow_id: UUID,
        status_value: FollowStatus,
    ):
        if status_value not in (FollowStatus.accepted, FollowStatus.declined):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Follow request can only be accepted or declined",
            )

        stmt = (
            update(FollowModel)
            .where(
                FollowModel.id == follow_id,
                FollowModel.following_id == user_id,
                FollowModel.status == FollowStatus.pending,
            )
            .values(status=status_value)
            .returning(FollowModel.id)
        )
        try:
            updated_id = await session.scalar(stmt)
            if not updated_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pending follow request not found",
                )
            await session.flush()
            return await FollowsRepository.get_by_id(session, follow_id)
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[FollowsRepository] update_request_status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating follow request",
            )
