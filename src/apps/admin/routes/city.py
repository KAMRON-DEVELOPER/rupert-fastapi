from uuid import UUID

from fastapi import status

from src.apps.locations.repositories import CityRepository
from src.apps.shared.schemas import CityRequest, CityResponse, MessageResponse
from src.core.database import sessionDep

from .router import admin_router


@admin_router.post(
    "/locations/{country_id}/cities",
    status_code=status.HTTP_201_CREATED,
    response_model=CityResponse,
)
async def create_city(session: sessionDep, country_id: UUID, schm: CityRequest):
    return await CityRepository.create(session, country_id, schm.name)


@admin_router.patch(
    "/locations/{country_id}/cities/{city_id}", response_model=MessageResponse
)
async def update_city(
    session: sessionDep, country_id: UUID, city_id: UUID, schm: CityRequest
):
    await CityRepository.update(session, country_id, city_id, schm.name)
    await session.commit()
    return MessageResponse(message="City updated successfully")


@admin_router.delete(
    "/locations/{country_id}/cities/{city_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_city(session: sessionDep, country_id: UUID, city_id: UUID):
    await CityRepository.delete(session, country_id, city_id)
    await session.commit()
