from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.analysis_status import AnalysisStatus
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel


@dataclass(slots=True)
class DocumentAnalysis:
    id: int | None
    document_id: int
    source_filename: str
    source_mime_type: str
    source_document_url: str
    source_size_bytes: int
    model_name: str
    status: AnalysisStatus = AnalysisStatus.RUNNING
    risk_level: AnalysisRiskLevel | None = None
    secrets_risk: SecretsRiskLevel | None = None
    personal_data_risk: AnalysisRiskLevel | None = None
    confidence: AnalysisConfidence | None = None
    tampering_suspected: bool = False
    data_categories: list[str] = field(default_factory=list)
    estimated_subjects: EstimatedSubjects = EstimatedSubjects.UNKNOWN
    summary: str = ""
    rationale: str = ""
    findings: list[AnalysisFinding] = field(default_factory=list)
    sanitized_content: dict[str, object] | list[object] | None = None
    content_truncated: bool = False
    error_message: str | None = None
    analyzed_at: datetime | None = None
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
        if self.source_size_bytes <= 0:
            raise ValueError("Source document size must be a positive number")
        if not self.model_name.strip():
            raise ValueError("Model name is required")
        if self.status == AnalysisStatus.COMPLETED:
            if (
                self.risk_level is None
                or self.secrets_risk is None
                or self.personal_data_risk is None
            ):
                raise ValueError("Completed analyses require all risk values")
            if (
                self.confidence is None
                or not self.summary.strip()
                or not self.rationale.strip()
            ):
                raise ValueError(
                    "Completed analyses require confidence, summary and rationale"
                )
        if (
            self.status == AnalysisStatus.FAILED
            and not (self.error_message or "").strip()
        ):
            raise ValueError("Failed analyses require a safe error message")

    @classmethod
    def create_pending(
        cls,
        *,
        document_id: int,
        source_filename: str,
        source_mime_type: str,
        source_document_url: str,
        source_size_bytes: int,
        model_name: str,
    ) -> "DocumentAnalysis":
        return cls(
            id=None,
            document_id=document_id,
            source_filename=source_filename,
            source_mime_type=source_mime_type,
            source_document_url=source_document_url,
            source_size_bytes=source_size_bytes,
            model_name=model_name,
        )

    def complete(
        self,
        *,
        risk_level: AnalysisRiskLevel,
        secrets_risk: SecretsRiskLevel,
        personal_data_risk: AnalysisRiskLevel,
        confidence: AnalysisConfidence,
        tampering_suspected: bool,
        data_categories: list[str],
        estimated_subjects: EstimatedSubjects,
        summary: str,
        rationale: str,
        findings: list[AnalysisFinding],
        sanitized_content: dict[str, object] | list[object],
        content_truncated: bool,
    ) -> None:
        if not summary.strip() or not rationale.strip():
            raise ValueError("Completed analysis summary and rationale are required")
        now = datetime.now(UTC)
        self.status = AnalysisStatus.COMPLETED
        self.risk_level = risk_level
        self.secrets_risk = secrets_risk
        self.personal_data_risk = personal_data_risk
        self.confidence = confidence
        self.tampering_suspected = tampering_suspected
        self.data_categories = sorted(set(data_categories))
        self.estimated_subjects = estimated_subjects
        self.summary = summary.strip()
        self.rationale = rationale.strip()
        self.findings = list(findings)
        self.sanitized_content = sanitized_content
        self.content_truncated = content_truncated
        self.error_message = None
        self.analyzed_at = now
        self.updated_at = now

    def fail(self, safe_error_message: str) -> None:
        if not safe_error_message.strip():
            raise ValueError("A safe analysis error message is required")
        self.status = AnalysisStatus.FAILED
        self.risk_level = None
        self.secrets_risk = None
        self.personal_data_risk = None
        self.confidence = None
        self.summary = ""
        self.rationale = ""
        self.error_message = safe_error_message.strip()
        self.analyzed_at = None
        self.updated_at = datetime.now(UTC)

    @property
    def explanation(self) -> str:
        return " ".join(part for part in (self.summary, self.rationale) if part).strip()
