from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class DocumentUploadedEvent:
    event_id: UUID = field(default_factory=uuid4)
    document_id: int = 0
    owner_user_id: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")
        if self.owner_user_id <= 0:
            raise ValueError("Owner user ID must be a positive number")

