from pprint import pprint

from fastapi import HTTPException

from src.apps.users.repositories.session import SessionsRepository
from src.apps.users.repositories.user import UsersRepository
from src.apps.users.schemas.user import UserDetail, UserUpdateRequest
from src.core.database import DBSession
from src.core.logger import logger
from src.core.settings import get_settings
from src.dependencies.proactive_refresh import authDep

from .router import users_router

settings = get_settings()


@users_router.get("/", response_model=UserDetail)
async def get_user(auth: authDep, session: DBSession):
    user_id, _, _ = auth

    try:
        user = await UsersRepository.get_by_id(user_id, session)
        logger.debug(f"user.email_verified: {user.email_verified}")
        logger.debug(f"user.skills: {user.skills}")
        logger.debug(f"user.resumes: {user.resumes}")
        logger.debug(f"user.work_experiences: {user.work_experiences}")
        return user
    except Exception as e:
        logger.error("get_user UsersRepository.get_by_id")
        pprint(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@users_router.patch("/")
async def update_user(auth: authDep, schm: UserUpdateRequest, session: DBSession):
    user_id, _, _ = auth

    try:
        return await UsersRepository.update_by_id(user_id, schm, session)
    except Exception as e:
        logger.error("update_user UsersRepository.update_by_id")
        pprint(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@users_router.delete("/")
async def delete_user(auth: authDep, session: DBSession):
    user_id, _, refresh_token = auth

    try:
        await SessionsRepository.delete(user_id, refresh_token, session)
        await UsersRepository.delete_by_id(user_id, session)
    except Exception as e:
        logger.error("update_user [SessionsRepository.delete, UsersRepository.delete_by_id]")
        pprint(e)
        raise HTTPException(status_code=500, detail="Something went wrong")
