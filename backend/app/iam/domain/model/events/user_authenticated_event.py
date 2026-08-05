from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class UserAuthenticatedEvent:
    event_id: UUID = field(default_factory=uuid4)
    username: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValueError("Authenticated username is required")
