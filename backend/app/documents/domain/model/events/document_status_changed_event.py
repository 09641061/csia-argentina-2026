from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.documents.domain.model.valueobjects.document_status import DocumentStatus


@dataclass(frozen=True, slots=True)
class DocumentStatusChangedEvent:
    event_id: UUID = field(default_factory=uuid4)
    document_id: int = 0
    new_status: DocumentStatus = DocumentStatus.UPLOADED
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")

