import asyncio
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.apps.__init__ import Base
from src.core.logger import logger
from src.core.settings import get_settings

settings = get_settings()


engine: AsyncEngine = create_async_engine(
    settings.database.url, echo=False, pool_size=settings.database.pool_size
)
session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session() as s:
        yield s


sessionDep = Annotated[AsyncSession, Depends(get_session)]


async def setup_db():
    logger.debug("Database is initializing")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(setup_db())
