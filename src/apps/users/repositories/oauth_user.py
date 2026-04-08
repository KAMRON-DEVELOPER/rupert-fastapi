from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import OAuthUserModel


class OAuthUsersRepository:
    @staticmethod
    async def find_providers_by_user_id(user_id: UUID, session: AsyncSession):
        stmt = select(OAuthUserModel.provider).where(OAuthUserModel.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()
