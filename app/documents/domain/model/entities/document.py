from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType
from app.documents.domain.model.valueobjects.document_name import DocumentName
from app.documents.domain.model.valueobjects.document_size_bytes import DocumentSizeBytes
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.model.valueobjects.document_storage_path import DocumentStoragePath


@dataclass(slots=True)
class Document:
    id: int | None
    owner_user_id: int
    name: DocumentName
    original_filename: str
    mime_type: DocumentMimeType
    size_bytes: DocumentSizeBytes
    storage_path: DocumentStoragePath
    status: DocumentStatus = DocumentStatus.UPLOADED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    analyzed_at: datetime | None = None
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if self.id is not None and self.id <= 0:
            raise ValueError("Document ID must be a positive number")
        if self.owner_user_id <= 0:
            raise ValueError("Owner user ID must be a positive number")
        if not self.original_filename.strip():
            raise ValueError("Original filename is required")

    @classmethod
    def create(
        cls,
        *,
        owner_user_id: int,
        name: str,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
    ) -> "Document":
        return cls(
            id=None,
            owner_user_id=owner_user_id,
            name=DocumentName(name),
            original_filename=original_filename,
            mime_type=DocumentMimeType(mime_type),
            size_bytes=DocumentSizeBytes(size_bytes),
            storage_path=DocumentStoragePath(storage_path),
        )

    def mark_processing(self) -> None:
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.now(UTC)

    def mark_analyzed(self) -> None:
        self.status = DocumentStatus.ANALYZED
        self.analyzed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def mark_blocked(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("Blocked reason is required")
        self.status = DocumentStatus.BLOCKED
        self.blocked_reason = reason
        self.updated_at = datetime.now(UTC)
