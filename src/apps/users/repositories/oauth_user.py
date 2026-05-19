from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.schemas.enums import Provider
from src.apps.users.models import OAuthUserModel
from src.core.logger import logger


class OAuthUsersRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        provider_id: str,
        user_id: UUID,
        provider: Provider,
        username: str | None = None,
        email: str | None = None,
        picture: str | None = None,
    ):
        record = OAuthUserModel(
            provider_id=provider_id,
            user_id=user_id,
            provider=provider,
            username=username,
            email=email,
            picture=picture,
        )

        try:
            session.add(record)
            await session.flush()
            return record
        except Exception as e:
            await session.rollback()
            logger.error(f"[OAuthUsersRepository] create: {e}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating oauth user",
            )

    @staticmethod
    async def find_providers_by_user_id(
        session: AsyncSession, user_id: UUID
    ) -> Sequence[Provider]:
        stmt = select(OAuthUserModel.provider).where(
            OAuthUserModel.user_id == user_id
        )

        try:
            result = await session.scalars(stmt)
            return result.all()
        except Exception as e:
            logger.error(
                f"[OAuthUsersRepository] find_providers_by_user_id: {e}"
            )
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while searching oauth user by email",
            )

    @staticmethod
    async def get_by_provider_id(
        session: AsyncSession, provider_id: str, required=True
    ):
        stmt = select(OAuthUserModel).where(
            OAuthUserModel.provider_id == provider_id
        )

        try:
            record = await session.scalar(stmt)

            if not record and required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OAuth user not found by the provider id",
                )

            return record
        except Exception as e:
            logger.error(f"[OAuthUsersRepository] get_by_id: {e}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving oauth user by provider id",
            )
