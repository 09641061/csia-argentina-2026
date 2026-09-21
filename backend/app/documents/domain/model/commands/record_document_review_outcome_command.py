from dataclasses import dataclass

from app.documents.domain.model.valueobjects.document_status import DocumentStatus


@dataclass(frozen=True, slots=True)
class RecordDocumentReviewOutcomeCommand:
    """Closes the document lifecycle once the security review reached a verdict."""

    document_id: int
    status: DocumentStatus
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")
        if self.status == DocumentStatus.BLOCKED and not (self.blocked_reason or "").strip():
            raise ValueError("A blocked document requires a safe reason")
