from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.shared.models import SkillModel
from src.apps.shared.schemas import PaginatedResponse
from src.apps.shared.schemas.skill import (
    SkillLinkCreateRequest,
    SkillLinkResponse,
)
from src.apps.users.models import ResumeModel, ResumeSkillLink
from src.core.logger import logger

OPTIONS = selectinload(ResumeSkillLink.skill).load_only(
    SkillModel.id, SkillModel.created_at, SkillModel.updated_at, SkillModel.name
)


class ResumeSkillsRepository:
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

    @staticmethod
    async def get_many(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedResponse[SkillLinkResponse]:
        await ResumeSkillsRepository._enforce_ownership(
            session, user_id, resume_id
        )

        clause = ResumeSkillLink.resume_id == resume_id

        stmt = (
            select(ResumeSkillLink)
            .options(OPTIONS)
            .where(clause)
            .order_by(ResumeSkillLink.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total_stmt = select(func.count(ResumeSkillLink.id)).where(clause)

        try:
            records = (await session.scalars(stmt)).all()
            data = [
                SkillLinkResponse.model_validate(record) for record in records
            ]
            total = await session.scalar(total_stmt) or 0

            return PaginatedResponse(data=data, total=total)
        except Exception as e:
            logger.error(f"[ResumeSkillsRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving resume skills",
            )

    @staticmethod
    async def get(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        skill_link_id: UUID,
    ):
        await ResumeSkillsRepository._enforce_ownership(
            session, user_id, resume_id
        )

        stmt = (
            select(ResumeSkillLink)
            .options(OPTIONS)
            .where(
                ResumeSkillLink.id == skill_link_id,
                ResumeSkillLink.resume_id == resume_id,
            )
        )

        try:
            return (await session.scalars(stmt)).one()
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume skill link not found",
            )
        except Exception as e:
            logger.error(f"[ResumeSkillsRepository] get: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving resume skill",
            )

    @staticmethod
    async def get_optional(
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        skill_link_id: UUID,
    ):
        await ResumeSkillsRepository._enforce_ownership(
            session, user_id, resume_id
        )

        stmt = (
            select(ResumeSkillLink)
            .options(OPTIONS)
            .where(
                ResumeSkillLink.id == skill_link_id,
                ResumeSkillLink.resume_id == resume_id,
            )
        )

        try:
            return await session.scalar(stmt)
        except Exception as e:
            logger.error(f"[ResumeSkillsRepository] get_optional: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving resume skill",
            )

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
