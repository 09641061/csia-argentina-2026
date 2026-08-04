from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel


@dataclass(frozen=True, slots=True)
class DocumentAnalysisCompletedEvent:
    event_id: UUID = field(default_factory=uuid4)
    analysis_id: int = 0
    document_id: int = 0
    risk_level: AnalysisRiskLevel = AnalysisRiskLevel.LOW
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.analysis_id <= 0:
            raise ValueError("Analysis ID must be a positive number")
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")

