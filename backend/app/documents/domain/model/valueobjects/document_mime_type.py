from dataclasses import dataclass
from typing import ClassVar

from app.documents.domain.exceptions import UnsupportedDocumentTypeError


@dataclass(frozen=True, slots=True)
class DocumentMimeType:
    """MIME type of an uploaded document. JSON is the only supported type."""

    value: str

    JSON: ClassVar[str] = "application/json"

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Document MIME type is required")

        normalized = self.value.split(";", maxsplit=1)[0].strip().lower()

        if normalized != self.JSON:
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type: {normalized}. Only {self.JSON} is accepted"
            )

        object.__setattr__(self, "value", normalized)
