from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.users.models import UserModel


class UsersRepository:
    @staticmethod
    async def find_by_email(email: str, session: AsyncSession):
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(email: str, password_hash: Optional[str], first_name: str, last_name: str, session: AsyncSession):
        record = UserModel(email=email, password_hash=password_hash, first_name=first_name, last_name=last_name)
        session.add(record)
        await session.flush()
        return record
