from dataclasses import dataclass

from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_finding_severity import (
    AnalysisFindingSeverity,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)


@dataclass(frozen=True, slots=True)
class AnalysisFinding:
    finding_id: str
    finding_type: AnalysisFindingType
    severity: AnalysisFindingSeverity
    title: str
    description: str
    json_path: str
    evidence: str
    detection_method: str
    confidence: AnalysisConfidence
    occurrences: int = 1
    data_category: str | None = None
    is_placeholder: bool = False

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Finding ID is required")
        if not self.title.strip():
            raise ValueError("Finding title is required")
        if not self.description.strip():
            raise ValueError("Finding description is required")
        if not self.json_path.startswith("$"):
            raise ValueError("Finding JSONPath must start with $")
        if not self.evidence.strip():
            raise ValueError("Masked finding evidence is required")
        if not self.detection_method.strip():
            raise ValueError("Finding detection method is required")
        if self.occurrences <= 0:
            raise ValueError("Finding occurrences must be positive")

    @property
    def masked_evidence(self) -> str:
        return self.evidence
