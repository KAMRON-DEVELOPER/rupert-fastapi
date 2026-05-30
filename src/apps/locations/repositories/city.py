from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.models import CityModel
from src.apps.shared.schemas import CityResponse, PaginatedResponse
from src.core.logger import logger


class CityRepository:
    @classmethod
    async def create(cls, session: AsyncSession, country_id: UUID, name: str):
        record = CityModel(country_id=country_id, name=name)

        try:
            session.add(record)
            await session.flush()
            await session.commit()
            return record
        except IntegrityError as e:
            logger.error(f"[CityRepository] create: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="City already exist",
            )

    @classmethod
    async def update(
        cls, session: AsyncSession, country_id: UUID, city_id: UUID, name: str
    ):
        stmt = (
            update(CityModel)
            .where(CityModel.id == city_id, CityModel.country_id == country_id)
            .values({"name": name})
            .returning(CityModel.id)
        )

        try:
            updated_city_id = await session.scalar(stmt)

            if not updated_city_id:
                logger.error("City not found to update")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="City not found to update",
                )

            return updated_city_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[CityRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating city",
            )

    @classmethod
    async def delete(
        cls, session: AsyncSession, country_id: UUID, city_id: UUID
    ):
        stmt = (
            delete(CityModel)
            .where(CityModel.country_id == country_id)
            .where(CityModel.id == city_id)
            .returning(CityModel.id)
        )

        try:
            deleted_city_id = await session.scalar(stmt)

            if not deleted_city_id:
                logger.error("City not found to delete")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="City not found to delete",
                )

            return deleted_city_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[CityRepository] delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating city",
            )

    @classmethod
    async def get_many(
        cls, session: AsyncSession, country_id: UUID, limit: int, offset: int
    ) -> PaginatedResponse[CityResponse]:
        stmt = (
            select(CityModel)
            .where(CityModel.country_id == country_id)
            .limit(limit)
            .offset(offset)
        )
        count_stmt = select(func.count()).select_from(CityModel)

        try:
            rows = (await session.scalars(stmt)).all()
            total = await session.scalar(count_stmt) or 0

            return PaginatedResponse(
                data=[CityResponse.model_validate(row) for row in rows],
                total=total,
            )
        except Exception as e:
            logger.error(f"[CityRepository] get_many: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while retrieving cities",
            )
