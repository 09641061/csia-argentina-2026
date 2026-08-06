from dataclasses import dataclass

from app.iam.domain.model.valueobjects.username import Username


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    username: Username
    account_id: int | None = None

    @property
    def identity(self) -> str:
        return self.username.value
