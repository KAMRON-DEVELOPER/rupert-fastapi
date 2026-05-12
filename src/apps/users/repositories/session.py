from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import SessionModel


class SessionsRepository:
    @staticmethod
    async def create(
        user_id: UUID,
        user_agent: str | None,
        ip_addr: str | None,
        device_name: str | None,
        refresh_token: str,
        session: AsyncSession,
    ):
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

    @staticmethod
    async def delete(user_id: UUID, refresh_token: str, session: AsyncSession):
        stmt = delete(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.refresh_token == refresh_token,
            SessionModel.is_active,
        )
        await session.execute(stmt)
