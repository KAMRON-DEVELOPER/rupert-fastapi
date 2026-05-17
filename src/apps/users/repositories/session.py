from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import SessionModel
from src.core.logger import logger


class SessionsRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        refresh_token: str,
        user_id: UUID,
        user_agent: str | None = None,
        ip_addr: str | None = None,
        device_name: str | None = None,
    ):
        try:
            record = SessionModel(
                user_id=user_id,
                user_agent=user_agent,
                ip_addr=ip_addr,
                device_name=device_name,
                refresh_token=refresh_token,
            )
            session.add(record)
            await session.flush()
            return record
        except Exception as e:
            logger.error(f"[SessionsRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating session",
            )

    @staticmethod
    async def delete(
        session: AsyncSession, user_id: UUID, refresh_token: str
    ) -> None:
        try:
            stmt = (
                delete(SessionModel)
                .where(
                    SessionModel.user_id == user_id,
                    SessionModel.refresh_token == refresh_token,
                    SessionModel.is_active,
                )
                .returning(SessionModel.id)
            )
            result = await session.execute(stmt)
            affacted_row = result.scalar_one_or_none()

            if not affacted_row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session not found to delete",
                )

            await session.commit()
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"[SessionsRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting session",
            )

    @staticmethod
    async def get_by_user_id_and_token(
        session: AsyncSession, user_id: UUID, refresh_token: str
    ):
        try:
            stmt = select(SessionModel).where(
                SessionModel.user_id == user_id,
                SessionModel.refresh_token == refresh_token,
                SessionModel.is_active,
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()

            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or expired",
                )

            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[SessionsRepository] get_by_user_and_token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving session",
            )
