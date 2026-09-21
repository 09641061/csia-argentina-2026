from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.iam.domain.model.valueobjects.username import Username


@dataclass(frozen=True, slots=True)
class UserAccount:
    id: int | None
    username: Username
    password_hash: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.id is not None and self.id <= 0:
            raise ValueError("User account ID must be positive")
        if not self.password_hash.strip():
            raise ValueError("Password hash is required")
