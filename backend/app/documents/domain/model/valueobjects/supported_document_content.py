from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.documents.domain.exceptions import InvalidDocumentContentError
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType

MAX_IMAGE_PIXELS = 20_000_000


@dataclass(frozen=True, slots=True)
class SupportedDocumentContent:
    """
    Raw bytes whose signature and basic container match their normalized MIME.

    This validation deliberately happens before storage. Extraction performs a
    second, deeper validation later and remains fail-closed.
    """

    value: bytes
    mime_type: DocumentMimeType

    def __post_init__(self) -> None:
        if not self.value:
            raise InvalidDocumentContentError("Document content is required")

        validators = {
            DocumentMimeType.JSON: self._validate_json,
            DocumentMimeType.PNG: self._validate_image,
            DocumentMimeType.JPEG: self._validate_image,
            DocumentMimeType.WEBP: self._validate_image,
        }
        validators[self.mime_type.value]()

    @property
    def size_bytes(self) -> int:
        return len(self.value)

    def _validate_json(self) -> None:
        try:
            parsed = json.loads(self.value.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise InvalidDocumentContentError(
                "Document content must be UTF-8 encoded JSON"
            ) from error
        except json.JSONDecodeError as error:
            raise InvalidDocumentContentError(
                f"Document content is not valid JSON: {error.msg} "
                f"(line {error.lineno}, column {error.colno})"
            ) from error
        except RecursionError as error:
            raise InvalidDocumentContentError(
                "Document content is nested too deeply to be processed"
            ) from error
        if not isinstance(parsed, (dict, list)):
            raise InvalidDocumentContentError(
                "JSON content must be an object or an array"
            )

    def _validate_image(self) -> None:
        try:
            with Image.open(BytesIO(self.value)) as image:
                detected = (image.format or "").upper()
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise InvalidDocumentContentError(
                        "The uploaded image dimensions exceed the safe processing limit"
                    )
                image.verify()
        except InvalidDocumentContentError:
            raise
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError) as error:
            raise InvalidDocumentContentError("The uploaded image is corrupted") from error
        expected = {
            DocumentMimeType.PNG: "PNG",
            DocumentMimeType.JPEG: "JPEG",
            DocumentMimeType.WEBP: "WEBP",
        }[self.mime_type.value]
        if detected != expected:
            raise InvalidDocumentContentError(
                "The image bytes do not match the declared image type"
            )
