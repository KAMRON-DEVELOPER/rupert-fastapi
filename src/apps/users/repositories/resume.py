from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.shared.schemas import PaginatedResponse
from src.apps.users.models import ResumeModel
from src.apps.users.schemas.resume import ResumeResponse
from src.core.logger import logger

OPTIONS = (selectinload(ResumeModel.country), selectinload(ResumeModel.city))


class ResumesRepository:
    @staticmethod
    async def create(
        session: AsyncSession, user_id: UUID, values: dict
    ) -> ResumeModel:
        stmt = (
            insert(ResumeModel)
            .values({"user_id": user_id} | values)
            .returning(ResumeModel)
            .options(*OPTIONS)
        )

        try:
            return (await session.scalars(stmt)).one()
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ResumesRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resume data is invalid or contains duplicate skills",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumesRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating resume",
            )

    @staticmethod
    async def update(
        session: AsyncSession, user_id: UUID, resume_id: UUID, values: dict
    ) -> ResumeModel:

        stmt = (
            update(ResumeModel)
            .where(ResumeModel.id == resume_id, ResumeModel.user_id == user_id)
            .values(values)
            .returning(ResumeModel)
            .options(*OPTIONS)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ResumesRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resume data is invalid",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumesRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating resume",
            )

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, resume_id: UUID):
        stmt = (
            delete(ResumeModel)
            .where(ResumeModel.id == resume_id, ResumeModel.user_id == user_id)
            .returning(ResumeModel.id)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumesRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting resume",
            )

    @staticmethod
    async def get_many(
        session: AsyncSession, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> PaginatedResponse[ResumeResponse]:
        clause = ResumeModel.user_id == user_id

        stmt = (
            select(ResumeModel)
            .options(
                selectinload(ResumeModel.country),
                selectinload(ResumeModel.city),
            )
            .where(clause)
            .order_by(ResumeModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total_stmt = select(func.count(ResumeModel.id)).where(clause)

        try:
            records = (await session.scalars(stmt)).all()
            data = [ResumeResponse.model_validate(record) for record in records]
            total = await session.scalar(total_stmt) or 0

            return PaginatedResponse(data=data, total=total)
        except Exception as e:
            logger.error(f"[ResumesRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving resumes",
            )

    @staticmethod
    async def get(session: AsyncSession, user_id: UUID, resume_id: UUID):
        stmt = (
            select(ResumeModel)
            .options(*OPTIONS)
            .where(ResumeModel.id == resume_id, ResumeModel.user_id == user_id)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            logger.error("[ResumesRepository] get: resume not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )
        except MultipleResultsFound:
            logger.error(
                "[ResumesRepository] get: multiple rows for user_id={user_id}, resume_id={resume_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Multiple resume skill rows found",
            )
        except Exception as e:
            logger.error(f"[ResumesRepository] get_by_id_and_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving resume",
            )
