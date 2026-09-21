from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Access token is required")
        if self.expires_at.tzinfo is None:
            raise ValueError("Access token expiration must include a timezone")
        if self.expires_at <= datetime.now(UTC):
            raise ValueError("Access token expiration must be in the future")
