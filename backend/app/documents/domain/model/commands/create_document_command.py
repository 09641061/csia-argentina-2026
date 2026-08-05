from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateDocumentCommand:
    original_filename: str
    mime_type: str
    content: bytes

    def __post_init__(self) -> None:
        if not self.mime_type.strip():
            raise ValueError("Document MIME type is required")
        if not self.content:
            raise ValueError("Document content is required")

    @property
    def size_bytes(self) -> int:
        return len(self.content)
