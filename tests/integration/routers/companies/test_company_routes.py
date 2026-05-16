import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.companies.models import CompanyModel
from src.apps.shared.schemas.enums import CompanyStatus, CompanyType


@pytest.mark.asyncio
async def test_list_companies_happy_path(client: AsyncClient, session: AsyncSession):
    session.add(CompanyModel(name="Comp A", type=CompanyType.agency, status=CompanyStatus.approved))
    await session.commit()

    res = await client.get("/api/v1/companies/?limit=10&offset=0")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["data"][0]["name"] == "Comp A"


@pytest.mark.asyncio
async def test_list_companies_missing_pagination(client):
    res = await client.get("/api/v1/companies/")
    assert res.status_code == 422
