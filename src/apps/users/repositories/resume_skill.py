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
            ResumeModel.id == resume_id, ResumeModel.user_id == user_id
        )
        resume = await session.scalar(stmt)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )

    @staticmethod
    async def _get_links(
        session: AsyncSession,
        resume_id: UUID,
    ):
        stmt = (
            select(ResumeSkillLink)
            .options(selectinload(ResumeSkillLink.skill))
            .where(ResumeSkillLink.resume_id == resume_id)
            .order_by(ResumeSkillLink.created_at.desc())
        )
        return (await session.scalars(stmt)).all()

    @staticmethod
    async def create_batch(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        skills: list[dict],
    ):
        try:
            await ResumeSkillsRepository._ensure_resume_owned(
                session, user_id, resume_id
            )

            for skill in skills:
                session.add(ResumeSkillLink(resume_id=resume_id, **skill))

            await session.flush()

            return await ResumeSkillsRepository._get_links(session, resume_id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(
                f"[ResumeSkillsRepository] create_batch integrity: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more skills already exist or reference invalid skills",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] create_batch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating resume skills",
            )

    @staticmethod
    async def update_batch(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        skills: list[dict],
    ):
        try:
            await ResumeSkillsRepository._ensure_resume_owned(
                session, user_id, resume_id
            )

            for skill in skills:
                link_id: UUID = skill.pop("id")

                stmt = (
                    update(ResumeSkillLink)
                    .where(
                        ResumeSkillLink.id == link_id,
                        ResumeSkillLink.resume_id == resume_id,
                    )
                    .values(skill)
                    .returning(ResumeSkillLink.id)
                )
                updated_id = await session.scalar(stmt)

                if not updated_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Resume skill link {link_id} not found",
                    )

            await session.flush()

            return await ResumeSkillsRepository._get_links(session, resume_id)
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(
                f"[ResumeSkillsRepository] update_batch integrity: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more skills already exist or reference invalid skills",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] update_batch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating resume skills",
            )

    @staticmethod
    async def delete_batch(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        skill_link_ids: list[UUID],
    ):
        try:
            await ResumeSkillsRepository._ensure_resume_owned(
                session, user_id, resume_id
            )

            stmt = (
                delete(ResumeSkillLink)
                .where(
                    ResumeSkillLink.id.in_(skill_link_ids),
                    ResumeSkillLink.resume_id == resume_id,
                )
                .returning(ResumeSkillLink.id)
            )
            result = await session.execute(stmt)
            deleted_ids = [row[0] for row in result.all()]

            if not deleted_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No matching resume skill links found",
                )

            await session.flush()

            not_found_count = len(skill_link_ids) - len(deleted_ids)
            if not_found_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{not_found_count} skill link(s) not found",
                )

            return deleted_ids
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] delete_batch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting resume skills",
            )
