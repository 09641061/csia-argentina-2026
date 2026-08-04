from dataclasses import dataclass

from app.analysis.domain.model.valueobjects.analysis_finding_severity import AnalysisFindingSeverity
from app.analysis.domain.model.valueobjects.analysis_finding_type import AnalysisFindingType


@dataclass(frozen=True, slots=True)
class AnalysisFinding:
    finding_type: AnalysisFindingType
    severity: AnalysisFindingSeverity
    title: str
    description: str
    evidence: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Finding title is required")
        if not self.description.strip():
            raise ValueError("Finding description is required")
        if not self.evidence.strip():
            raise ValueError("Finding evidence is required")

