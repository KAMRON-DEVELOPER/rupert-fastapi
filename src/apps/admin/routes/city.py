from uuid import UUID

from fastapi import status

from src.apps.locations.repositories import CityRepository
from src.apps.shared.schemas.location import CityRequest
from src.core.database import sessionDep

from .router import admin_router


@admin_router.post(
    "/locations/{country_id}/cities", status_code=status.HTTP_201_CREATED
)
async def create_city(session: sessionDep, country_id: UUID, schm=CityRequest):
    return await CityRepository.create(session, country_id, schm.name)


@admin_router.patch("/locations/{country_id}/cities/{city_id}")
async def update_city(
    session: sessionDep, country_id: UUID, city_id: UUID, schm: CityRequest
):
    await CityRepository.update(session, country_id, city_id, schm.name)
    await session.commit()
