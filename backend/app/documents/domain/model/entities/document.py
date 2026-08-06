from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.documents.domain.model.valueobjects.document_display_name import (
    DocumentDisplayName,
)
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType
from app.documents.domain.model.valueobjects.document_size_bytes import (
    DocumentSizeBytes,
)
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.model.valueobjects.document_storage_reference import (
    DocumentStorageReference,
)


@dataclass(slots=True)
class Document:
    """A registered supported document. Documents never decides its content risk."""

    id: int | None
    display_name: DocumentDisplayName
    mime_type: DocumentMimeType
    size_bytes: DocumentSizeBytes
    storage_reference: DocumentStorageReference
    status: DocumentStatus = DocumentStatus.UPLOADED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    analyzed_at: datetime | None = None
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if self.id is not None and self.id <= 0:
            raise ValueError("Document ID must be a positive number")

    @classmethod
    def register(
        cls,
        *,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
        storage_reference: DocumentStorageReference,
    ) -> "Document":
        return cls(
            id=None,
            display_name=DocumentDisplayName.from_original_filename(original_filename),
            mime_type=DocumentMimeType(mime_type),
            size_bytes=DocumentSizeBytes(size_bytes),
            storage_reference=storage_reference,
        )

    def mark_processing(self) -> None:
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.now(UTC)

    def mark_analyzed(self) -> None:
        self.status = DocumentStatus.ANALYZED
        self.analyzed_at = datetime.now(UTC)
        self.updated_at = self.analyzed_at
        self.blocked_reason = None

    def mark_blocked(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("Blocked reason is required")
        self.status = DocumentStatus.BLOCKED
        self.blocked_reason = reason.strip()
        self.analyzed_at = datetime.now(UTC)
        self.updated_at = self.analyzed_at
