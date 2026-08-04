from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel


@dataclass(slots=True)
class DocumentAnalysis:
    id: int | None
    document_id: int
    source_filename: str
    source_mime_type: str
    source_document_url: str
    risk_level: AnalysisRiskLevel
    explanation: str
    model_name: str
    findings: list[AnalysisFinding] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.id is not None and self.id <= 0:
            raise ValueError("Analysis ID must be a positive number")
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")
        if not self.source_filename.strip():
            raise ValueError("Source filename is required")
        if not self.source_mime_type.strip():
            raise ValueError("Source MIME type is required")
        if not self.source_document_url.strip():
            raise ValueError("Source document URL is required")
        if not self.explanation.strip():
            raise ValueError("Analysis explanation is required")
        if not self.model_name.strip():
            raise ValueError("Model name is required")

    @classmethod
    def create(
        cls,
        *,
        document_id: int,
        source_filename: str,
        source_mime_type: str,
        source_document_url: str,
        risk_level: AnalysisRiskLevel,
        explanation: str,
        model_name: str,
        findings: list[AnalysisFinding],
    ) -> "DocumentAnalysis":
        return cls(
            id=None,
            document_id=document_id,
            source_filename=source_filename,
            source_mime_type=source_mime_type,
            source_document_url=source_document_url,
            risk_level=risk_level,
            explanation=explanation,
            model_name=model_name,
            findings=findings,
        )

