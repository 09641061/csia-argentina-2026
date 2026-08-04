from dataclasses import dataclass

from app.documents.domain.model.valueobjects.document_status import DocumentStatus


@dataclass(frozen=True, slots=True)
class UpdateDocumentStatusCommand:
    document_id: int
    status: DocumentStatus
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")

