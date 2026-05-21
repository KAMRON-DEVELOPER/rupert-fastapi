from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.users.models import ResumeModel, ResumeSkillLink
from src.core.logger import logger


class ResumeSkillsRepository:
    @staticmethod
    async def _ensure_resume_owned(
        session: AsyncSession, user_id: UUID, resume_id: UUID
    ):
        stmt = select(ResumeModel.id).where(
            ResumeModel.id == resume_id,
            ResumeModel.user_id == user_id,
        )
        resume = await session.scalar(stmt)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )

    @staticmethod
    async def _get_link(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        link_id: UUID,
        required: bool = True,
    ):
        await ResumeSkillsRepository._ensure_resume_owned(
            session, user_id, resume_id
        )
        stmt = (
            select(ResumeSkillLink)
            .options(selectinload(ResumeSkillLink.skill))
            .where(
                ResumeSkillLink.id == link_id,
                ResumeSkillLink.resume_id == resume_id,
            )
        )
        record = await session.scalar(stmt)
        if not record and required:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume skill link not found",
            )
        return record

    @staticmethod
    async def create(
        session: AsyncSession, user_id: UUID, resume_id: UUID, values: dict
    ):
        try:
            await ResumeSkillsRepository._ensure_resume_owned(
                session, user_id, resume_id
            )
            record = ResumeSkillLink(resume_id=resume_id, **values)
            session.add(record)
            await session.flush()
            return await ResumeSkillsRepository._get_link(
                session, user_id, resume_id, record.id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resume skill already exists or references invalid skill",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating resume skill",
            )

    @staticmethod
    async def update(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        link_id: UUID,
        values: dict,
    ):
        try:
            await ResumeSkillsRepository._get_link(
                session, user_id, resume_id, link_id
            )
            if values:
                stmt = (
                    update(ResumeSkillLink)
                    .where(
                        ResumeSkillLink.id == link_id,
                        ResumeSkillLink.resume_id == resume_id,
                    )
                    .values(values)
                    .returning(ResumeSkillLink.id)
                )
                await session.scalar(stmt)
                await session.flush()

            return await ResumeSkillsRepository._get_link(
                session, user_id, resume_id, link_id
            )
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resume skill data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating resume skill",
            )

    @staticmethod
    async def delete(
        session: AsyncSession, user_id: UUID, resume_id: UUID, link_id: UUID
    ):
        try:
            await ResumeSkillsRepository._ensure_resume_owned(
                session, user_id, resume_id
            )
            stmt = (
                delete(ResumeSkillLink)
                .where(
                    ResumeSkillLink.id == link_id,
                    ResumeSkillLink.resume_id == resume_id,
                )
                .returning(ResumeSkillLink.id)
            )
            deleted_id = await session.scalar(stmt)

            if not deleted_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resume skill link not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting resume skill",
            )
