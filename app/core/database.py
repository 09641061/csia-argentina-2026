from collections.abc import AsyncIterator
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import get_settings
from app.documents.infrastructure.persistence.sqlalchemy.models.base import Base

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_async_engine(settings.database_url, future=True, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def initialize_database() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    except Exception as error:
        logger.warning("Database initialization skipped: %s", error)
