from uuid import UUID

from fastapi import status

from src.apps.locations.repositories import CountryRepository
from src.apps.shared.schemas import (
    CountryCreateRequest,
    CountryResponse,
    CountryUpdateRequest,
    MessageResponse,
)
from src.core.database import sessionDep

from .router import admin_router


@admin_router.post(
    "/locations/countries",
    status_code=status.HTTP_201_CREATED,
    response_model=CountryResponse,
)
async def create_country(session: sessionDep, schm: CountryCreateRequest):
    return await CountryRepository.create(
        session, code=schm.code, name=schm.name
    )


@admin_router.patch(
    "/locations/countries/{country_id}", response_model=MessageResponse
)
async def update_country(
    session: sessionDep, country_id: UUID, schm: CountryUpdateRequest
):
    await CountryRepository.update(
        session, country_id, schm.model_dump(exclude_unset=True)
    )
    await session.commit()
    return MessageResponse(message="Country updated successfully")


@admin_router.delete(
    "/locations/countries/{country_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_country(session: sessionDep, country_id: UUID):
    await CountryRepository.delete(session, country_id)
    await session.commit()
