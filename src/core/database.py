import asyncio
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.apps.__init__ import Base
from src.core.logger import logger
from src.core.settings import get_settings

settings = get_settings()


async_engine: AsyncEngine = create_async_engine(settings.database.url, echo=False, pool_size=settings.database.pool_size)
async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as s:
        yield s


DBSession = Annotated[AsyncSession, Depends(get_session)]


async def initialize_db():
    logger.debug("Database is initializing...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(initialize_db())
