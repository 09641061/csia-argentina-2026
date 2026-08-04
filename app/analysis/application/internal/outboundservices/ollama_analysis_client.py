from dataclasses import dataclass
from typing import Protocol

from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.source_document_reference import SourceDocumentReference


@dataclass(frozen=True, slots=True)
class OllamaAnalysisInterpretation:
    risk_level: AnalysisRiskLevel
    summary: str
    rationale: str


class OllamaAnalysisClient(Protocol):
    async def analyze(
        self,
        *,
        source: SourceDocumentReference,
        extracted_text: str,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation:
        ...

