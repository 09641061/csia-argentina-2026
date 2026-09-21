from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.analysis_status import AnalysisStatus
from app.analysis.domain.model.valueobjects.analyzed_content_type import (
    AnalyzedContentType,
)
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel


@dataclass(slots=True)
class SecurityAnalysis:
    """
    One security review execution over a prompt or a supported document.

    The original content is never part of this entity. Only a fingerprint, a
    masked preview, masked findings and the risk assessment survive, so the
    audit trail can explain a decision without holding the very data the product
    exists to protect.
    """

    id: int | None
    content_type: AnalyzedContentType
    content_reference: str
    content_fingerprint: str
    content_length: int
    masked_preview: str
    model_name: str
    requested_by: str
    document_id: int | None = None
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
    content_truncated: bool = False
    error_message: str | None = None
    analyzed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.id is not None and self.id <= 0:
            raise ValueError("Analysis ID must be a positive number")
        if not self.content_reference.strip():
            raise ValueError("Content reference is required")
        if len(self.content_fingerprint) != 64:
            raise ValueError("Content fingerprint must be a SHA-256 hexadecimal digest")
        if self.content_length <= 0:
            raise ValueError("Content length must be a positive number")
        if not self.model_name.strip():
            raise ValueError("Model name is required")
        if not self.requested_by.strip():
            raise ValueError("Authenticated user is required")
        if self.content_type == AnalyzedContentType.DOCUMENT and not self.document_id:
            raise ValueError("A document analysis requires its document identifier")
        if self.content_type == AnalyzedContentType.PROMPT and self.document_id is not None:
            raise ValueError("A prompt analysis cannot reference a document")
        if self.status == AnalysisStatus.COMPLETED:
            if (
                self.risk_level is None
                or self.secrets_risk is None
                or self.personal_data_risk is None
                or self.confidence is None
            ):
                raise ValueError("Completed analyses require all risk values")
            if not self.summary.strip() or not self.rationale.strip():
                raise ValueError("Completed analyses require summary and rationale")
        if self.status == AnalysisStatus.FAILED and not (self.error_message or "").strip():
            raise ValueError("Failed analyses require a safe error message")

    @classmethod
    def start_for_prompt(
        cls,
        *,
        content_reference: str,
        content_fingerprint: str,
        content_length: int,
        masked_preview: str,
        model_name: str,
        requested_by: str,
    ) -> "SecurityAnalysis":
        return cls(
            id=None,
            content_type=AnalyzedContentType.PROMPT,
            content_reference=content_reference,
            content_fingerprint=content_fingerprint,
            content_length=content_length,
            masked_preview=masked_preview,
            model_name=model_name,
            requested_by=requested_by,
        )

    @classmethod
    def start_for_document(
        cls,
        *,
        document_id: int,
        content_reference: str,
        content_fingerprint: str,
        content_length: int,
        masked_preview: str,
        model_name: str,
        requested_by: str,
    ) -> "SecurityAnalysis":
        return cls(
            id=None,
            content_type=AnalyzedContentType.DOCUMENT,
            document_id=document_id,
            content_reference=content_reference,
            content_fingerprint=content_fingerprint,
            content_length=content_length,
            masked_preview=masked_preview,
            model_name=model_name,
            requested_by=requested_by,
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
        self.content_truncated = content_truncated
        self.error_message = None
        self.analyzed_at = now
        self.updated_at = now

    def fail(self, safe_error_message: str) -> None:
        """
        Close a run that could not be verified.

        Every risk value is cleared on purpose: an unverifiable execution must
        never be readable as a low-risk result later on.
        """

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
    def is_completed(self) -> bool:
        return self.status == AnalysisStatus.COMPLETED

    @property
    def explanation(self) -> str:
        if self.status == AnalysisStatus.FAILED:
            return self.error_message or "The security review could not be completed."
        return " ".join(part for part in (self.summary, self.rationale) if part).strip()

    @property
    def has_confirmed_sensitive_findings(self) -> bool:
        """
        Whether the deterministic scan confirmed real sensitive material.

        Placeholders and documentation examples are excluded, and low-severity
        context such as an isolated IP address does not count as confirmed.
        """

        return any(
            not finding.is_placeholder and finding.severity.value != "low"
            for finding in self.findings
        )
