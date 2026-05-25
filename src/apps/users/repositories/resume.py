from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.users.models import ResumeModel, ResumeSkillLink
from src.core.logger import logger


class ResumesRepository:
    @staticmethod
    async def create(
        session: AsyncSession, user_id: UUID, values: dict, skills: list[dict]
    ):
        record = ResumeModel(user_id=user_id, **values)

        try:
            session.add(record)
            await session.flush()

            for skill in skills:
                session.add(ResumeSkillLink(resume_id=record.id, **skill))

            await session.flush()

            return await ResumesRepository.get_by_id_and_user_id(
                session, user_id, record.id
            )
        except HTTPException:
            raise
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
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        values: dict,
        skills: list[dict] | None = None,
    ):
        await ResumesRepository.get_by_id_and_user_id(
            session, user_id, resume_id
        )

        try:
            if values:
                stmt = (
                    update(ResumeModel)
                    .where(
                        ResumeModel.id == resume_id,
                        ResumeModel.user_id == user_id,
                    )
                    .values(values)
                    .returning(ResumeModel.id)
                )
                await session.scalar(stmt)

            if skills:
                await session.execute(
                    delete(ResumeSkillLink).where(
                        ResumeSkillLink.resume_id == resume_id
                    )
                )
                await session.flush()

                for skill in skills:
                    session.add(ResumeSkillLink(resume_id=resume_id, **skill))

            await session.flush()

            return await ResumesRepository.get_by_id_and_user_id(
                session, user_id, resume_id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ResumesRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resume data is invalid or contains duplicate skills",
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
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resume not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumesRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting resume",
            )

    @staticmethod
    async def list_by_user_id(session: AsyncSession, user_id: UUID):
        stmt = (
            select(ResumeModel)
            .where(ResumeModel.user_id == user_id)
            .order_by(ResumeModel.updated_at.desc())
        )

        try:
            return (await session.scalars(stmt)).all()
        except Exception as e:
            logger.error(f"[ResumesRepository] list_by_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving resumes",
            )

    @staticmethod
    async def get_by_id_and_user_id(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        required: bool = True,
    ):
        stmt = (
            select(ResumeModel)
            .options(
                selectinload(ResumeModel.skill_links).selectinload(
                    ResumeSkillLink.skill
                )
            )
            .where(ResumeModel.id == resume_id, ResumeModel.user_id == user_id)
        )
        try:
            record = await session.scalar(stmt)

            if not record and required:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resume not found",
                )

            return record
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ResumesRepository] get_by_id_and_user_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving resume",
            )
