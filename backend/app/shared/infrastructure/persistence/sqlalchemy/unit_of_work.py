from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyUnitOfWork:
    """
    Explicit transaction boundary for the application services.

    Repositories only stage changes; the application service decides when a
    consistent checkpoint has been reached. This keeps a security decision and
    its audit record atomic, and prevents a half-written execution from being
    committed by an unrelated repository call.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
