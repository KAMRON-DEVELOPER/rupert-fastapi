# from datetime import date

# import pytest
# from sqlalchemy import select
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.ext.asyncio import AsyncSession

# from src.apps.companies.models import CompanyModel
# from src.apps.companies.repositories.company import CompaniesRepository
# from src.apps.companies.schemas.company import CompanyListParams
# from src.apps.shared.schemas import PaginationQuery
# from src.apps.shared.schemas.enums import (
#     ApplicationStatus,
#     CompanyStatus,
#     CompanyType,
#     JobSearchStatus,
#     Specialization,
#     SubmissionType,
#     VacancyStatus,
#     WorkFormat,
# )
# from src.apps.users.models import ActivityModel, SessionModel
# from src.apps.users.repositories.session import SessionsRepository
# from src.apps.users.repositories.user import UsersRepository
# from src.apps.users.schemas.user import UserUpdateRequest
# from src.apps.vacancies.models import VacancyModel
# from src.apps.vacancies.repositories.vacancy import VacanciesRepository
# from src.apps.vacancies.schemas.application import ApplicationListParams
# from src.apps.vacancies.schemas.vacancy import VacancyListParams


# @pytest.mark.anyio
# async def test_create_user_success(db_session):
#     user = await UsersRepository.create(
#         email="test@example.com",
#         password_hash="hashed_pw",
#         first_name="John",
#         last_name="Doe",
#         session=db_session,
#     )
#     assert user.id is not None
#     assert user.email == "test@example.com"
#     assert user.first_name == "John"


# @pytest.mark.anyio
# async def test_create_user_duplicate_email_raises_error(db_session):
#     await UsersRepository.create(
#         email="duplicate@example.com",
#         password_hash="pw",
#         first_name="A",
#         last_name="B",
#         session=db_session,
#     )

#     with pytest.raises(IntegrityError):
#         await UsersRepository.create(
#             email="duplicate@example.com",
#             password_hash="pw2",
#             first_name="C",
#             last_name="D",
#             session=db_session,
#         )


# @pytest.mark.anyio
# async def test_update_user_mutation(db_session):
#     # Setup
#     user = await UsersRepository.create(
#         email="update@example.com",
#         password_hash="pw",
#         first_name="Old",
#         last_name="Name",
#         session=db_session,
#     )
#     await db_session.commit()  # Commit to finalize the insert

#     # Execute Mutation
#     update_data = UserUpdateRequest(
#         first_name="New",
#         headline="Python Dev",
#         specialization=Specialization.backend,
#     )
#     updated_user = await UsersRepository.update_by_id(
#         id=user.id, schm=update_data, session=db_session
#     )

#     # Assert
#     assert updated_user.first_name == "New"
#     assert updated_user.headline == "Python Dev"
#     assert updated_user.specialization == Specialization.backend
#     # Ensure un-updated fields remain intact
#     assert updated_user.last_name == "Name"


# @pytest.mark.anyio
# async def test_delete_user_cascade(db_session):
#     # Setup
#     user = await UsersRepository.create(
#         email="delete@example.com",
#         password_hash="pw",
#         first_name="A",
#         last_name="B",
#         session=db_session,
#     )
#     await db_session.commit()

#     # Execute
#     await UsersRepository.delete_by_id(id=user.id, session=db_session)
#     await db_session.commit()

#     # Assert
#     deleted_user = await UsersRepository.find_by_email(
#         "delete@example.com", db_session
#     )
#     assert deleted_user is None


# @pytest.mark.asyncio
# async def test_users_repository_crud_and_stats(
#     session: AsyncSession, make_user
# ):
#     """
#     Coverage:
#         create
#         find_by_email
#         get_by_id, update_by_id
#         set_email_verified
#         get_stats
#         delete_by_id
#     """

#     user = await UsersRepository.create(
#         "repo@example.com", "hash", "A", "B", session
#     )
#     await session.commit()

#     found = await UsersRepository.find_by_email("repo@example.com", session)
#     assert found and found.id == user.id

#     loaded = await UsersRepository.get_by_id(user.id, session)
#     assert loaded.email == "repo@example.com"

#     updated = await UsersRepository.update_by_id(
#         user.id, UserUpdateRequest(headline="New"), session
#     )
#     await session.commit()
#     assert updated.headline == "New"

#     await UsersRepository.set_email_verified(user.id, session)
#     await session.commit()
#     assert (
#         await UsersRepository.get_by_id(user.id, session)
#     ).email_verified is True

#     extra = await make_user(
#         email="stats@example.com",
#         job_search_status=JobSearchStatus.actively_looking,
#     )
#     session.add(ActivityModel(user_id=extra.id, activity_date=date.today()))
#     await session.commit()

#     stats = await UsersRepository.get_stats(session)
#     assert stats.total == 2
#     assert stats.looking_for_job_count == 1
#     assert len(stats.dau_chart) == 30

#     await UsersRepository.delete_by_id(user.id, session)
#     await session.commit()
#     assert (
#         await UsersRepository.find_by_email("repo@example.com", session) is None
#     )


# @pytest.mark.asyncio
# async def test_sessions_repository_create_and_delete(
#     session: AsyncSession, make_user
# ):
#     user = await make_user(email="session@example.com")
#     record = await SessionsRepository.create(
#         user.id, "pytest", "127.0.0.1", "dev", "r-token", session
#     )
#     await session.commit()

#     assert record.user_id == user.id
#     assert (
#         await session.execute(select(SessionModel))
#     ).scalar_one().refresh_token == "r-token"

#     await SessionsRepository.delete(user.id, "r-token", session)
#     await session.commit()

#     assert (await session.execute(select(SessionModel))).scalars().all() == []


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


# @pytest.mark.asyncio
# async def test_vacancies_repository_methods(session: AsyncSession, make_user):
#     user = await make_user(email="applicant@example.com")
#     company = CompanyModel(
#         name="VacCo",
#         type=CompanyType.product_company,
#         status=CompanyStatus.approved,
#         country="US",
#         city="NY",
#     )
#     session.add(company)
#     await session.flush()

#     created = await VacanciesRepository.create(
#         session,
#         company.id,
#         {
#             "title": "Python Dev",
#             "description": "desc",
#             "submission_type": SubmissionType.profile,
#             "specialization": Specialization.backend,
#             "work_format": WorkFormat.remote,
#             "status": VacancyStatus.open,
#         },
#     )

#     listed = await VacanciesRepository.get_many(
#         session,
#         PaginationQuery(limit=10, offset=0),
#         VacancyListParams(status=VacancyStatus.open),
#     )
#     assert listed.total == 1

#     single = await VacanciesRepository.get_by_id(session, created.id)
#     assert single.title == "Python Dev"

#     updated = await VacanciesRepository.update(
#         session, created.id, {"title": "Senior Python Dev"}
#     )
#     assert updated and updated.title == "Senior Python Dev"

#     app = await VacanciesRepository.apply_to_vacancy(
#         session,
#         user.id,
#         {
#             "vacancy_id": created.id,
#             "cover_letter": "hello",
#             "status": ApplicationStatus.pending,
#         },
#     )
#     assert app.id is not None

#     applications = await VacanciesRepository.get_applications(
#         session,
#         PaginationQuery(limit=10, offset=0),
#         ApplicationListParams(vacancy_id=created.id),
#     )
#     assert applications.total == 1

#     loaded_app = await VacanciesRepository.get_application_by_id(
#         session, app.id
#     )
#     assert loaded_app.id == app.id

#     changed = await VacanciesRepository.update_application_status(
#         session, app.id, ApplicationStatus.viewed, "ok"
#     )
#     assert changed and changed.status == ApplicationStatus.viewed

#     stats = await VacanciesRepository.get_stats(session)
#     assert stats.total == 1
#     assert stats.open == 1

#     assert await VacanciesRepository.delete(session, created.id) is True
#     assert (await session.execute(select(VacancyModel))).scalars().all() == []
