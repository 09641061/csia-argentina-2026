from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentMimeType:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Document MIME type is required")

