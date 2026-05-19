from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import SessionModel
from src.core.logger import logger


class SessionsRepository:
    @staticmethod
    async def list_by_user_id(session: AsyncSession, user_id: UUID):
        stmt = (
            select(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.is_active.is_(True),
            )
            .order_by(SessionModel.last_activity_at.desc())
        )

        try:
            return (await session.scalars(stmt)).all()
        except Exception as e:
            logger.error(f"[SessionsRepository] list_by_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving sessions",
            )

    @staticmethod
    async def create(
        session: AsyncSession,
        refresh_token: str,
        user_id: UUID,
        user_agent: str | None = None,
        ip_addr: str | None = None,
        device_name: str | None = None,
    ):
        record = SessionModel(
            user_id=user_id,
            user_agent=user_agent,
            ip_addr=ip_addr,
            device_name=device_name,
            refresh_token=refresh_token,
        )

        try:
            session.add(record)
            await session.flush()
            return record
        except Exception as e:
            await session.rollback()
            logger.error(f"[SessionsRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating session",
            )

    @staticmethod
    async def delete(
        session: AsyncSession, user_id: UUID, refresh_token: str
    ) -> None:
        stmt = (
            delete(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.refresh_token == refresh_token,
                SessionModel.is_active.is_(True),
            )
            .returning(SessionModel.id)
        )

        try:
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session not found to delete",
                )

            await session.flush()
        except HTTPException as e:
            raise e
        except Exception as e:
            await session.rollback()
            logger.error(f"[SessionsRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting session",
            )

    @staticmethod
    async def delete_by_id(
        session: AsyncSession, user_id: UUID, session_id: UUID
    ) -> str:
        stmt = (
            delete(SessionModel)
            .where(
                SessionModel.id == session_id,
                SessionModel.user_id == user_id,
                SessionModel.is_active.is_(True),
            )
            .returning(SessionModel.refresh_token)
        )

        try:
            deleted_refresh_token = await session.scalar(stmt)

            if not deleted_refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found",
                )

            await session.flush()
            return deleted_refresh_token
        except HTTPException as e:
            raise e
        except Exception as e:
            await session.rollback()
            logger.error(f"[SessionsRepository] delete_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting session",
            )

    @staticmethod
    async def delete_all_by_user_id(
        session: AsyncSession,
        user_id: UUID,
        except_refresh_token: str | None = None,
    ) -> int:
        stmt = delete(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.is_active.is_(True),
        )

        if except_refresh_token:
            stmt = stmt.where(
                SessionModel.refresh_token != except_refresh_token
            )

        stmt = stmt.returning(SessionModel.id)

        try:
            deleted_ids = (await session.scalars(stmt)).all()
            await session.flush()
            return len(deleted_ids)
        except Exception as e:
            await session.rollback()
            logger.error(f"[SessionsRepository] delete_all_by_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting sessions",
            )

    @staticmethod
    async def replace_refresh_token(
        session: AsyncSession,
        user_id: UUID,
        old_refresh_token: str,
        new_refresh_token: str,
    ) -> None:
        stmt = (
            update(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.refresh_token == old_refresh_token,
                SessionModel.is_active.is_(True),
            )
            .values(refresh_token=new_refresh_token)
            .returning(SessionModel.id)
        )

        try:
            updated_id = await session.scalar(stmt)

            if not updated_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session not found or expired",
                )

            await session.flush()
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[SessionsRepository] replace_refresh_token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while refreshing session",
            )

    @staticmethod
    async def get_by_user_id_and_token(
        session: AsyncSession, user_id: UUID, refresh_token: str, required=True
    ):
        stmt = select(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.refresh_token == refresh_token,
            SessionModel.is_active.is_(True),
        )

        try:
            record = await session.scalar(stmt)

            if not record and required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session not found or expired",
                )

            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[SessionsRepository] get_by_user_id_and_token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving session",
            )
