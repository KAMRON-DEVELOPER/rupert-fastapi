from uuid import UUID

from fastapi import APIRouter

from src.apps.locations.repositories import CityRepository, CountryRepository
from src.apps.shared.schemas import (
    CityResponse,
    CountryResponse,
    PaginatedResponse,
    paginationDep,
)
from src.core.database import sessionDep

locations_router = APIRouter()


@locations_router.get(
    "/countries", response_model=PaginatedResponse[CountryResponse]
)
async def list_countries(session: sessionDep, pagination: paginationDep):
    return await CountryRepository.get_many(
        session, pagination.limit, pagination.offset
    )


@locations_router.get(
    "/countries/{country_id}/cities",
    response_model=PaginatedResponse[CityResponse],
)
async def list_cities(
    session: sessionDep, country_id: UUID, pagination: paginationDep
):
    return await CityRepository.get_many(
        session, country_id, pagination.limit, pagination.offset
    )
