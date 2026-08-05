from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class DocumentAnalysisFailedEvent:
    event_id: UUID = field(default_factory=uuid4)
    analysis_id: int = 0
    document_id: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.analysis_id <= 0 or self.document_id <= 0:
            raise ValueError("Analysis and document IDs must be positive numbers")
