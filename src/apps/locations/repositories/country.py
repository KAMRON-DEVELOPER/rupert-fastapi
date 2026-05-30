from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import CountryModel
from src.apps.shared.schemas import CountryResponse, PaginatedResponse
from src.core.logger import logger


class CountryRepository:
    @classmethod
    async def create(cls, session: AsyncSession, code: str, name: str):
        record = CountryModel(code=code, name=name)

        try:
            session.add(record)
            await session.flush()
            await session.commit()
            return record
        except IntegrityError as e:
            logger.error(f"[CountryRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Country already exist",
            )

    @classmethod
    async def update(
        cls, session: AsyncSession, country_id: UUID, values: dict
    ):
        stmt = (
            update(CountryModel)
            .where(CountryModel.id == country_id)
            .values(values)
            .returning(CountryModel.id)
        )

        try:
            updated_country_id = await session.scalar(stmt)

            if not updated_country_id:
                logger.error("Country not found to update")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Country not found to update",
                )

            return updated_country_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[CountryRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating country",
            )

    @classmethod
    async def delete(cls, session: AsyncSession, country_id: UUID):
        stmt = (
            delete(CountryModel)
            .where(CountryModel.id == country_id)
            .returning(CountryModel.id)
        )

        try:
            deleated_country_id = await session.scalar(stmt)

            if not deleated_country_id:
                logger.error("Country not found to delete")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Country not found to delete",
                )

            return deleated_country_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[CountryRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating country",
            )

    @classmethod
    async def get_many(
        cls, session: AsyncSession, limit: int, offset: int
    ) -> PaginatedResponse[CountryResponse]:
        stmt = select(CountryModel).limit(limit).offset(offset)
        count_stmt = select(func.count()).select_from(CountryModel)

        try:
            rows = (await session.scalars(stmt)).all()
            total = await session.scalar(count_stmt) or 0

            return PaginatedResponse(
                data=[CountryResponse.model_validate(row) for row in rows],
                total=total,
            )
        except Exception as e:
            logger.error(f"[CountryRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving countries",
            )
