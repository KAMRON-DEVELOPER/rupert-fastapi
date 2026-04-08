from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.schemas import UserUpdateSchema
from src.apps.users.models import UserModel


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
    async def update_by_id(id: UUID, schema: UserUpdateSchema, session: AsyncSession):
        stmt = update(UserModel).where(UserModel.id == id).values({})
        result = await session.execute(stmt)
        return result.scalar_one()
