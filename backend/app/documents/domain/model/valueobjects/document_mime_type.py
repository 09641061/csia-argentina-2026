from dataclasses import dataclass
from pathlib import PurePath
from typing import ClassVar

from app.documents.domain.exceptions import UnsupportedDocumentTypeError


@dataclass(frozen=True, slots=True)
class DocumentMimeType:
    """Normalized MIME type of a document Claude can review locally."""

    value: str

    JSON: ClassVar[str] = "application/json"
    PNG: ClassVar[str] = "image/png"
    JPEG: ClassVar[str] = "image/jpeg"
    WEBP: ClassVar[str] = "image/webp"

    SUPPORTED: ClassVar[frozenset[str]] = frozenset({JSON, PNG, JPEG, WEBP})
    EXTENSION_TYPES: ClassVar[dict[str, str]] = {
        ".json": JSON,
        ".png": PNG,
        ".jpg": JPEG,
        ".jpeg": JPEG,
        ".webp": WEBP,
    }

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Document MIME type is required")

        normalized = self.value.split(";", maxsplit=1)[0].strip().lower()
        if normalized == "image/jpg":
            normalized = self.JPEG

        if normalized not in self.SUPPORTED:
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type: {normalized}. Supported formats: "
                "JSON, PNG, JPEG and WebP"
            )

        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_upload(cls, declared_mime_type: str, filename: str) -> "DocumentMimeType":
        """Use a browser MIME when possible and a known extension only as fallback."""

        normalized = declared_mime_type.split(";", maxsplit=1)[0].strip().lower()
        if normalized in {
            "",
            "application/octet-stream",
            "binary/octet-stream",
            "text/plain",
        }:
            extension = PurePath(filename).suffix.lower()
            inferred = cls.EXTENSION_TYPES.get(extension)
            if inferred is None:
                raise UnsupportedDocumentTypeError(
                    "The document type could not be inferred from its filename"
                )
            normalized = inferred
        return cls(normalized)

    @property
    def is_image(self) -> bool:
        return self.value in {self.PNG, self.JPEG, self.WEBP}
