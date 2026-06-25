from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.schemas import PaginatedResponse
from src.apps.users.models import WorkExperienceModel
from src.apps.users.schemas.work_experience import WorkExperienceResponse
from src.core.logger import logger


class WorkExperiencesRepository:
    @staticmethod
    async def create(session: AsyncSession, user_id: UUID, values: dict):
        record = WorkExperienceModel(user_id=user_id, **values)
        try:
            session.add(record)
            await session.flush()
            return record
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[WorkExperiencesRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid work experience data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[WorkExperiencesRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating work experience",
            )

    @staticmethod
    async def update(
        session: AsyncSession, user_id: UUID, id: UUID, values: dict
    ):
        await WorkExperiencesRepository.get(session, user_id, id)
        if not values:
            return await WorkExperiencesRepository.get(session, user_id, id)

        stmt = (
            update(WorkExperienceModel)
            .where(
                WorkExperienceModel.id == id,
                WorkExperienceModel.user_id == user_id,
            )
            .values(values)
            .returning(WorkExperienceModel.id)
        )
        try:
            await session.scalar(stmt)
            await session.flush()
            return await WorkExperiencesRepository.get(session, user_id, id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[WorkExperiencesRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid work experience data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[WorkExperiencesRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating work experience",
            )

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, id: UUID):
        stmt = (
            delete(WorkExperienceModel)
            .where(
                WorkExperienceModel.id == id,
                WorkExperienceModel.user_id == user_id,
            )
            .returning(WorkExperienceModel.id)
        )
        try:
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Work experience not found",
                )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[WorkExperiencesRepository] delete integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete work experience due to related records",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[WorkExperiencesRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting work experience",
            )

    @staticmethod
    async def get_many(
        session: AsyncSession, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> PaginatedResponse[WorkExperienceResponse]:
        clause = WorkExperienceModel.user_id == user_id

        stmt = (
            select(WorkExperienceModel)
            .where(clause)
            .order_by(WorkExperienceModel.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total_stmt = select(func.count(WorkExperienceModel.id)).where(clause)

        try:
            records = (await session.scalars(stmt)).all()
            data = [
                WorkExperienceResponse.model_validate(record)
                for record in records
            ]
            total = await session.scalar(total_stmt) or 0

            return PaginatedResponse(data=data, total=total)
        except Exception as e:
            logger.error(f"[WorkExperiencesRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving work experiences",
            )

    @staticmethod
    async def get(session: AsyncSession, user_id: UUID, id: UUID):
        stmt = select(WorkExperienceModel).where(
            WorkExperienceModel.id == id, WorkExperienceModel.user_id == user_id
        )
        try:
            record = await session.scalar(stmt)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Work experience not found",
                )
            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[WorkExperiencesRepository] get: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving work experience",
            )

    @staticmethod
    async def get_optional(session: AsyncSession, user_id: UUID, id: UUID):
        stmt = select(WorkExperienceModel).where(
            WorkExperienceModel.id == id, WorkExperienceModel.user_id == user_id
        )
        try:
            return await session.scalar(stmt)
        except Exception as e:
            logger.error(f"[WorkExperiencesRepository] get_optional: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving work experience",
            )

    @staticmethod
    async def list_by_user_id(session: AsyncSession, user_id: UUID):
        stmt = (
            select(WorkExperienceModel)
            .where(WorkExperienceModel.user_id == user_id)
            .order_by(WorkExperienceModel.started_at.desc())
        )
        try:
            return (await session.scalars(stmt)).all()
        except Exception as e:
            logger.error(f"[WorkExperiencesRepository] list_by_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving work experiences",
            )
