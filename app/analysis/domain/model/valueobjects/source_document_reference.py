from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceDocumentReference:
    document_id: int
    original_filename: str
    mime_type: str
    document_url: str

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")
        if not self.original_filename.strip():
            raise ValueError("Original filename is required")
        if not self.mime_type.strip():
            raise ValueError("Document MIME type is required")
        if not self.document_url.strip():
            raise ValueError("Document URL is required")

