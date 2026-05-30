import asyncio
from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import SkillModel
from src.core.logger import logger


class SkillRepository:
    @classmethod
    async def create(cls, session: AsyncSession, name: str):
        record = SkillModel(name=name)

        try:
            session.add(record)
            await session.flush()
            await session.commit()
            return record
        except IntegrityError as e:
            logger.error(f"[SkillRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill already exist",
            )

    @classmethod
    async def update(cls, session: AsyncSession, skill_id: UUID, name: str):
        stmt = (
            update(SkillModel)
            .where(SkillModel.id == skill_id)
            .values({"name": name})
            .returning(SkillModel.id)
        )

        try:
            updated_skill_id = await session.scalar(stmt)

            if not updated_skill_id:
                logger.error("Skill not found to update")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Skill not found to update",
                )

            return updated_skill_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[SkillRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating skill",
            )

    @classmethod
    async def delete(cls, session: AsyncSession, skill_id: UUID):
        stmt = (
            delete(SkillModel)
            .where(SkillModel.id == skill_id)
            .returning(SkillModel.id)
        )

        try:
            deleated_skill_id = await session.scalar(stmt)

            if not deleated_skill_id:
                logger.error("Skill not found to delete")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Skill not found to delete",
                )

            return deleated_skill_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[SkillRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating skill",
            )

    @classmethod
    async def get_many(
        cls, session: AsyncSession, limit: int, offset: int
    ) -> tuple[Sequence[SkillModel], int]:
        stmt = select(SkillModel).limit(limit).offset(offset)
        count_stmt = select(func.count()).select_from(SkillModel)

        try:
            rows, total = await asyncio.gather(
                session.scalars(stmt),
                session.scalar(count_stmt),
            )

            return rows.all(), total or 0
        except Exception as e:
            logger.error(f"[SkillRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving skills",
            )
