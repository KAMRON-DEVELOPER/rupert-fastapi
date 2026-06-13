from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.shared.models import SkillModel
from src.apps.shared.schemas.skill import SkillLinkCreateRequest
from src.apps.users.models import ResumeModel, ResumeSkillLink
from src.core.logger import logger

OPTIONS = selectinload(ResumeSkillLink.skill).load_only(
    SkillModel.id, SkillModel.name
)


class ResumeSkillsRepository:
    @staticmethod
    async def _enforce_ownership(
        session: AsyncSession, user_id: UUID, resume_id: UUID
    ) -> None:
        """
        Verifies that the resume exists and belongs to the current user.
        Raises an HTTP 404 error if the record is missing or unauthorized.
        """
        stmt = select(ResumeModel.id).where(
            ResumeModel.id == resume_id, ResumeModel.user_id == user_id
        )

        resume_exists = await session.scalar(stmt)

        if not resume_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        schm: SkillLinkCreateRequest,
    ):
        await ResumeSkillsRepository._enforce_ownership(
            session, user_id, resume_id
        )

        stmt = (
            insert(ResumeSkillLink)
            .values(
                resume_id=resume_id,
                skill_id=schm.skill_id,
                proficiency=schm.proficiency,
                last_used_at=schm.last_used_at,
            )
            .returning(ResumeSkillLink)
            .options(OPTIONS)
        )

        try:
            return (await session.scalars(stmt)).one()
        except HTTPException:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] create integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more skills already exist or reference invalid skills",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while creating resume skills",
            )

    @staticmethod
    async def update(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        skill_link_id: UUID,
        values: dict,
    ):
        await ResumeSkillsRepository._enforce_ownership(
            session, user_id, resume_id
        )

        stmt = (
            update(ResumeSkillLink)
            .where(
                ResumeSkillLink.id == skill_link_id,
                ResumeSkillLink.resume_id == resume_id,
            )
            .values(values)
            .returning(ResumeSkillLink)
            .options(OPTIONS)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume skill link not found",
            )
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] update integrity: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid resume skill data",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating resume skills",
            )

    @staticmethod
    async def delete(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        skill_link_id: UUID,
    ) -> UUID:
        await ResumeSkillsRepository._enforce_ownership(
            session, user_id, resume_id
        )

        stmt = (
            delete(ResumeSkillLink)
            .where(
                ResumeSkillLink.id == skill_link_id,
                ResumeSkillLink.resume_id == resume_id,
            )
            .returning(ResumeSkillLink.id)
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume skill link not found",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"[ResumeSkillsRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while deleting resume skills",
            )
