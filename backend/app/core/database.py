import logging
from collections.abc import AsyncIterator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import get_settings
from app.shared.infrastructure.persistence.sqlalchemy.base import Base

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_async_engine(
    settings.database_url, future=True, echo=False, pool_pre_ping=True
)
async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def initialize_database() -> None:
    """
    Create the schema before serving traffic.

    A database problem is a hard failure: the API must never start looking
    healthy while it cannot store an audit trail of the security decisions.
    """

    # Imported for their side effect: every table must be registered on Base
    # before create_all runs.
    from app.analysis.infrastructure.persistence.sqlalchemy.models import (  # noqa: F401
        security_analysis_model,
    )
    from app.chat.infrastructure.persistence.sqlalchemy.models import (  # noqa: F401
        conversation_model,
        message_model,
    )
    from app.decision.infrastructure.persistence.sqlalchemy.models import (  # noqa: F401
        secure_interaction_model,
    )
    from app.iam.infrastructure.persistence.sqlalchemy.models import (  # noqa: F401
        user_account_model,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await _migrate_ownership_columns(connection)
    logger.info("Database schema is ready")


async def _migrate_ownership_columns(connection) -> None:
    """Add MVP ownership columns to databases created by earlier revisions."""

    for table_name in ("security_analyses", "secure_interactions"):
        columns = await connection.run_sync(
            lambda sync_connection, table=table_name: {
                column["name"] for column in inspect(sync_connection).get_columns(table)
            }
        )
        if "requested_by" not in columns:
            await connection.execute(
                text(
                    f"ALTER TABLE {table_name} "
                    "ADD COLUMN requested_by VARCHAR(64) NOT NULL DEFAULT 'legacy'"
                )
            )
        await connection.execute(
            text(
                f"CREATE INDEX IF NOT EXISTS ix_{table_name}_requested_by "
                f"ON {table_name} (requested_by)"
            )
        )


async def check_database_connection() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception as error:  # noqa: BLE001 - health probe must never raise
        logger.warning("Database health check failed: %s", type(error).__name__)
        return False
