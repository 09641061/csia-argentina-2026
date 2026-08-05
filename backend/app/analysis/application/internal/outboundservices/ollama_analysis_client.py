from typing import Protocol

from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.document_structure_summary import (
    DocumentStructureSummary,
)
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.source_document_reference import (
    SourceDocumentReference,
)


class OllamaAnalysisClient(Protocol):
    async def analyze(
        self,
        *,
        source: SourceDocumentReference,
        structure: DocumentStructureSummary,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation: ...
