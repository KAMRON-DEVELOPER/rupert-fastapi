from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.shared.models import SkillModel
from src.apps.shared.schemas import PaginatedResponse
from src.apps.shared.schemas.skill import SkillLinkResponse
from src.apps.users.models import UserSkillLink
from src.core.logger import logger

OPTIONS = selectinload(UserSkillLink.skill).load_only(
    SkillModel.id, SkillModel.created_at, SkillModel.updated_at, SkillModel.name
)


class UserSkillsRepository:
    @staticmethod
    async def create(
        session: AsyncSession, user_id: UUID, values: dict
    ) -> UserSkillLink:
        stmt = (
            insert(UserSkillLink)
            .values({"user_id": user_id} | values)
            .returning(UserSkillLink)
            .options(OPTIONS)
        )

        try:
            return (await session.scalars(stmt)).one()
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
        session: AsyncSession, user_id: UUID, skill_link_id: UUID, values: dict
    ) -> UserSkillLink:
        stmt = (
            update(UserSkillLink)
            .where(
                UserSkillLink.id == skill_link_id,
                UserSkillLink.user_id == user_id,
            )
            .values(values)
            .returning(UserSkillLink)
            .options(OPTIONS)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User skill link not found",
            )
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
    async def delete(
        session: AsyncSession, user_id: UUID, skill_link_id: UUID
    ) -> UUID:
        stmt = (
            delete(UserSkillLink)
            .where(
                UserSkillLink.id == skill_link_id,
                UserSkillLink.user_id == user_id,
            )
            .returning(UserSkillLink.id)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User skill link not found",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[UserSkillsRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting user skill",
            )

    @staticmethod
    async def get_many(
        session: AsyncSession, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> PaginatedResponse[SkillLinkResponse]:
        clause = UserSkillLink.user_id == user_id

        stmt = (
            select(UserSkillLink)
            .options(OPTIONS)
            .where(clause)
            .order_by(UserSkillLink.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total_stmt = select(func.count(UserSkillLink.id)).where(clause)

        try:
            records = (await session.scalars(stmt)).all()
            data = [
                SkillLinkResponse.model_validate(record) for record in records
            ]
            total = await session.scalar(total_stmt) or 0

            return PaginatedResponse(data=data, total=total)
        except Exception as e:
            logger.error(f"[UserSkillsRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user skills",
            )

    @staticmethod
    async def get(
        session: AsyncSession, user_id: UUID, skill_link_id: UUID
    ) -> UserSkillLink:
        stmt = (
            select(UserSkillLink)
            .options(OPTIONS)
            .where(
                UserSkillLink.id == skill_link_id,
                UserSkillLink.user_id == user_id,
            )
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            logger.error("[UserSkillsRepository] get: user skill not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User skill link not found",
            )
        except MultipleResultsFound:
            logger.error(
                "[UserSkillsRepository] get: multiple rows for skill_link_id={skill_link_id} user_id={user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Multiple user skill rows found",
            )
        except Exception as e:
            logger.error(f"[UserSkillsRepository] get: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user skill",
            )

    @staticmethod
    async def get_optional(
        session: AsyncSession, user_id: UUID, skill_link_id: UUID
    ) -> UserSkillLink | None:
        stmt = (
            select(UserSkillLink)
            .options(selectinload(UserSkillLink.skill))
            .where(
                UserSkillLink.id == skill_link_id,
                UserSkillLink.user_id == user_id,
            )
        )

        try:
            return await session.scalar(stmt)
        except Exception as e:
            logger.error(f"[UserSkillsRepository] get_optional: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving user skill",
            )
