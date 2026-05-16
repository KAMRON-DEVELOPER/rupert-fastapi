# import pytest

# from src.apps.companies.models import CompanyModel
# from src.apps.shared.schemas.enums import (
#     ApplicationStatus,
#     CompanyStatus,
#     CompanyType,
#     Specialization,
#     SubmissionType,
#     VacancyStatus,
#     WorkFormat,
# )
# from src.apps.vacancies.models import ApplicationModel, VacancyModel


# @pytest.mark.asyncio
# async def test_list_and_get_application(client, session, make_user):
#     user = await make_user(email="app@example.com")
#     company = CompanyModel(
#         name="AppCmp",
#         type=CompanyType.enterprise,
#         status=CompanyStatus.approved,
#         country="US",
#         city="NY",
#     )
#     session.add(company)
#     await session.flush()
#     vacancy = VacancyModel(
#         company_id=company.id,
#         title="Role",
#         description="desc",
#         submission_type=SubmissionType.profile,
#         specialization=Specialization.backend,
#         work_format=WorkFormat.remote,
#         status=VacancyStatus.open,
#     )
#     session.add(vacancy)
#     await session.flush()
#     application = ApplicationModel(
#         applicant_id=user.id,
#         vacancy_id=vacancy.id,
#         status=ApplicationStatus.pending,
#     )
#     session.add(application)
#     await session.commit()

#     res = await client.get("/api/v1/vacancies/applications?limit=10&offset=0")
#     assert res.status_code == 200
#     assert res.json()["total"] == 1

#     detail = await client.get(
#         f"/api/v1/vacancies/applications/{application.id}"
#     )
#     assert detail.status_code == 200
#     assert detail.json()["id"] == str(application.id)


# @pytest.mark.asyncio
# async def test_get_application_not_found(client):
#     res = await client.get(
#         "/api/v1/vacancies/applications/00000000-0000-0000-0000-000000000000"
#     )
#     assert res.status_code == 500
