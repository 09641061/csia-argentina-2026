from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.iam.domain.model.entities.user_account import UserAccount
from app.iam.domain.model.valueobjects.username import Username
from app.iam.domain.repositories.user_account_repository import UserAccountRepository
from app.iam.infrastructure.persistence.sqlalchemy.models.user_account_model import (
    UserAccountModel,
)


class SqlAlchemyUserAccountRepository(UserAccountRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_username(self, username: Username) -> UserAccount | None:
        result = await self._session.execute(
            select(UserAccountModel).where(UserAccountModel.username == username.value)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def save(self, account: UserAccount) -> UserAccount:
        model = UserAccountModel(
            username=account.username.value,
            password_hash=account.password_hash,
            created_at=account.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: UserAccountModel) -> UserAccount:
        return UserAccount(
            id=model.id,
            username=Username(model.username),
            password_hash=model.password_hash,
            created_at=model.created_at,
        )
