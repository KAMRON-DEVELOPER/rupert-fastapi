# from datetime import date

# @pytest.mark.asyncio
# async def test_companies_repository_methods(session: AsyncSession):
#     company = CompanyModel(
#         name="Acme",
#         type=CompanyType.startup,
#         status=CompanyStatus.approved,
#         country="US",
#         city="NYC",
#     )
#     session.add(company)
#     await session.flush()
#     vacancy = VacancyModel(
#         company_id=company.id,
#         title="Backend",
#         description="desc",
#         submission_type=SubmissionType.profile,
#         specialization=Specialization.backend,
#         work_format=WorkFormat.remote,
#         status=VacancyStatus.open,
#     )
#     session.add(vacancy)
#     await session.commit()
#     items = await CompaniesRepository.get_many(
#         session,
#         PaginationQuery(limit=10, offset=0),
#         CompanyListParams(name="Acme"),
#     )
#     assert items.total == 1
#     assert items.data[0].open_vacancies_count == 1
#     detail = await CompaniesRepository.get_by_id(session, company.id)
#     assert detail.member_count == 0
#     stats = await CompaniesRepository.get_stats(session)
#     assert stats.total == 1
#     assert stats.by_type[0].count == 1

# import pytest
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from src.apps.companies.models import CompanyModel
# from src.apps.companies.repositories.company import CompaniesRepository
# from src.apps.companies.schemas.company import CompanyListParams
# from src.apps.shared.schemas import PaginationQuery
# from src.apps.shared.schemas.enums import (  # Specialization,; SubmissionType,; VacancyStatus,; WorkFormat,
#     CompanyStatus,
#     CompanyType,
# )
# from src.apps.vacancies.models import VacancyModel


# @pytest.mark.asyncio
# async def test_list_companies_happy_path(client, session):
#     session.add(
#         CompanyModel(
#             name="Comp A",
#             type=CompanyType.agency,
#             status=CompanyStatus.approved,
#             country="US",
#             city="Tashkent",
#         )
#     )
#     await session.commit()

#     res = await client.get("/api/v1/companies/?limit=10&offset=0")
#     assert res.status_code == 200
#     body = res.json()
#     assert body["total"] == 1
#     assert body["data"][0]["name"] == "Comp A"


# @pytest.mark.asyncio
# async def test_list_companies_missing_pagination(client):
#     res = await client.get("/api/v1/companies/")
#     assert res.status_code == 422
