from typing import Protocol

from app.iam.domain.model.entities.user_account import UserAccount
from app.iam.domain.model.valueobjects.username import Username


class UserAccountRepository(Protocol):
    async def find_by_username(self, username: Username) -> UserAccount | None: ...

    async def save(self, account: UserAccount) -> UserAccount: ...
