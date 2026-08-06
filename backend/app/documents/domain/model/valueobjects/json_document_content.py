import json
from dataclasses import dataclass

from app.documents.domain.exceptions import InvalidDocumentContentError


@dataclass(frozen=True, slots=True)
class JsonDocumentContent:
    """
    Raw bytes of an uploaded document, proven to be a JSON object or array.

    The declared MIME type comes from the client and cannot be trusted, so the
    payload itself is parsed before the document is accepted.
    """

    value: bytes

    def __post_init__(self) -> None:
        if not self.value:
            raise InvalidDocumentContentError("Document content is required")

        try:
            decoded = self.value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise InvalidDocumentContentError(
                "Document content must be UTF-8 encoded JSON"
            ) from error

        try:
            parsed = json.loads(decoded)
        except json.JSONDecodeError as error:
            raise InvalidDocumentContentError(
                f"Document content is not valid JSON: {error.msg} (line {error.lineno}, column {error.colno})"
            ) from error
        except RecursionError as error:
            raise InvalidDocumentContentError(
                "Document content is nested too deeply to be processed"
            ) from error

        if not isinstance(parsed, (dict, list)):
            raise InvalidDocumentContentError(
                "Document content must be a JSON object or a JSON array"
            )

    @property
    def size_bytes(self) -> int:
        return len(self.value)
