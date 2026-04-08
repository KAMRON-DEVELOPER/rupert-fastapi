from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import SessionModel
from sqlalchemy import delete


class SessionsRepository:
    @staticmethod
    async def create(user_id: UUID, user_agent: Optional[str], ip_addr: Optional[str], device_name: Optional[str], refresh_token: str, session: AsyncSession):
        record = SessionModel(user_id=user_id, user_agent=user_agent, ip_addr=ip_addr, device_name=device_name, refresh_token=refresh_token)
        session.add(record)
        await session.flush()
        return record

    @staticmethod
    async def delete(user_id: UUID, refresh_token: str, session: AsyncSession):
        stmt = delete(SessionModel).where(SessionModel.user_id == user_id, SessionModel.refresh_token == refresh_token, SessionModel.is_active == True)
        return record
