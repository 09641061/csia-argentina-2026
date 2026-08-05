from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.analysis.domain.model.valueobjects.analyzed_content_type import AnalyzedContentType


@dataclass(frozen=True, slots=True)
class SecurityAnalysisFailedEvent:
    event_id: UUID = field(default_factory=uuid4)
    analysis_id: int = 0
    content_type: AnalyzedContentType = AnalyzedContentType.PROMPT
    document_id: int | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.analysis_id <= 0:
            raise ValueError("Analysis ID must be a positive number")
