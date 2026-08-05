from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateDocumentCommand:
    owner_user_id: int
    name: str
    original_filename: str
    mime_type: str
    size_bytes: int
    content: bytes

    def __post_init__(self) -> None:
        if self.owner_user_id <= 0:
            raise ValueError("Owner user ID must be a positive number")
        if not self.name.strip():
            raise ValueError("Document name is required")
        if not self.original_filename.strip():
            raise ValueError("Original filename is required")
        if not self.mime_type.strip():
            raise ValueError("Document MIME type is required")
        if self.size_bytes <= 0:
            raise ValueError("Document size must be a positive number")
        if not self.content:
            raise ValueError("Document content is required")

