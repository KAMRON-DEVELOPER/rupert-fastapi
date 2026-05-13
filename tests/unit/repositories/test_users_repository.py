from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.shared.schemas.enums import JobSearchStatus
from src.apps.users.models import ActivityModel, SessionModel
from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas.user import UserUpdateRequest


@pytest.mark.asyncio
async def test_users_repository_crud_and_stats(session: AsyncSession, make_user):
    user = await UsersRepository.create("repo@example.com", "hash", "A", "B", session)
    await session.commit()

    found = await UsersRepository.find_by_email("repo@example.com", session)
    assert found and found.id == user.id

    loaded = await UsersRepository.get_by_id(user.id, session)
    assert loaded.email == "repo@example.com"

    updated = await UsersRepository.update_by_id(user.id, UserUpdateRequest(headline="New"), session)
    await session.commit()
    assert updated.headline == "New"

    await UsersRepository.set_email_verified(user.id, session)
    await session.commit()
    assert (await UsersRepository.get_by_id(user.id, session)).email_verified is True

    extra = await make_user(email="stats@example.com", job_search_status=JobSearchStatus.actively_looking)
    session.add(ActivityModel(user_id=extra.id, activity_date=date.today()))
    await session.commit()

    stats = await UsersRepository.get_stats(session)
    assert stats.total == 2
    assert stats.looking_for_job_count == 1
    assert len(stats.dau_chart) == 30

    await UsersRepository.delete_by_id(user.id, session)
    await session.commit()
    assert await UsersRepository.find_by_email("repo@example.com", session) is None


@pytest.mark.asyncio
async def test_sessions_repository_create_and_delete(session: AsyncSession, make_user):
    user = await make_user(email="session@example.com")
    record = await SessionsRepository.create(user.id, "pytest", "127.0.0.1", "dev", "r-token", session)
    await session.commit()

    assert record.user_id == user.id
    assert (await session.execute(select(SessionModel))).scalar_one().refresh_token == "r-token"

    await SessionsRepository.delete(user.id, "r-token", session)
    await session.commit()

    assert (await session.execute(select(SessionModel))).scalars().all() == []
