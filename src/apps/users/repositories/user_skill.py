from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.users.models import UserSkillLink
from src.core.logger import logger


class UserSkillsRepository:
    @staticmethod
    async def list_by_user_id(session: AsyncSession, user_id: UUID):
        stmt = (
            select(UserSkillLink)
            .options(selectinload(UserSkillLink.skill))
            .where(UserSkillLink.user_id == user_id)
            .order_by(UserSkillLink.created_at.desc())
        )

        try:
            return (await session.scalars(stmt)).all()
        except Exception as e:
            logger.error(f"[UserSkillsRepository] list_by_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user skills",
            )

    @staticmethod
    async def get_by_id_and_user_id(
        session: AsyncSession,
        user_id: UUID,
        link_id: UUID,
        required: bool = True,
    ):
        stmt = (
            select(UserSkillLink)
            .options(selectinload(UserSkillLink.skill))
            .where(
                UserSkillLink.id == link_id, UserSkillLink.user_id == user_id
            )
        )

        try:
            record = await session.scalar(stmt)

            if not record and required:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User skill link not found",
                )

            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[UserSkillsRepository] get_by_id_and_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user skill",
            )

    @staticmethod
    async def create(session: AsyncSession, user_id: UUID, values: dict):
        record = UserSkillLink(user_id=user_id, **values)
        try:
            session.add(record)
            await session.flush()
            return await UserSkillsRepository.get_by_id_and_user_id(
                session, user_id, record.id
            )

        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[UserSkillsRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User skill already exists or references invalid skill",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[UserSkillsRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating user skill",
            )

    @staticmethod
    async def update(
        session: AsyncSession, user_id: UUID, link_id: UUID, values: dict
    ):
        await UserSkillsRepository.get_by_id_and_user_id(
            session, user_id, link_id
        )

        if not values:
            return await UserSkillsRepository.get_by_id_and_user_id(
                session, user_id, link_id
            )

        stmt = (
            update(UserSkillLink)
            .where(
                UserSkillLink.id == link_id, UserSkillLink.user_id == user_id
            )
            .values(values)
            .returning(UserSkillLink.id)
        )

        try:
            await session.scalar(stmt)
            await session.flush()

            return await UserSkillsRepository.get_by_id_and_user_id(
                session, user_id, link_id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[UserSkillsRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user skill data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[UserSkillsRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating user skill",
            )

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, link_id: UUID):
        stmt = (
            delete(UserSkillLink)
            .where(
                UserSkillLink.id == link_id, UserSkillLink.user_id == user_id
            )
            .returning(UserSkillLink.id)
        )

        try:
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User skill link not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[UserSkillsRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting user skill",
            )
