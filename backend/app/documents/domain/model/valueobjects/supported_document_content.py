from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from zipfile import BadZipFile, ZipFile, is_zipfile

import pymupdf
from PIL import Image, UnidentifiedImageError

from app.documents.domain.exceptions import InvalidDocumentContentError
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType

MAX_OFFICE_ARCHIVE_ENTRIES = 2_000
MAX_OFFICE_UNCOMPRESSED_BYTES = 40 * 1024 * 1024
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
            DocumentMimeType.PDF: self._validate_pdf,
            DocumentMimeType.DOCX: lambda: self._validate_office("word/document.xml"),
            DocumentMimeType.XLSX: lambda: self._validate_office("xl/workbook.xml"),
            DocumentMimeType.PNG: self._validate_image,
            DocumentMimeType.JPEG: self._validate_image,
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

    def _validate_pdf(self) -> None:
        if not self.value.startswith(b"%PDF-"):
            raise InvalidDocumentContentError("The file is not a valid PDF document")
        try:
            document = pymupdf.open(stream=self.value, filetype="pdf")
        except Exception as error:
            raise InvalidDocumentContentError("The PDF document is corrupted") from error
        try:
            if document.needs_pass:
                raise InvalidDocumentContentError(
                    "Password-protected PDF documents are not supported"
                )
            if document.page_count == 0:
                raise InvalidDocumentContentError("The PDF document has no pages")
        finally:
            document.close()

    def _validate_office(self, required_member: str) -> None:
        if not is_zipfile(BytesIO(self.value)):
            raise InvalidDocumentContentError("The Office document is not a valid ZIP container")
        try:
            with ZipFile(BytesIO(self.value)) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_OFFICE_ARCHIVE_ENTRIES:
                    raise InvalidDocumentContentError(
                        "The Office document contains too many embedded entries"
                    )
                total_size = sum(entry.file_size for entry in entries)
                if total_size > MAX_OFFICE_UNCOMPRESSED_BYTES:
                    raise InvalidDocumentContentError(
                        "The Office document expands beyond the safe processing limit"
                    )
                names = {entry.filename for entry in entries}
                if required_member not in names or "[Content_Types].xml" not in names:
                    raise InvalidDocumentContentError(
                        "The Office document does not match its declared format"
                    )
        except BadZipFile as error:
            raise InvalidDocumentContentError(
                "The Office document container is corrupted"
            ) from error

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
        expected = "PNG" if self.mime_type.value == DocumentMimeType.PNG else "JPEG"
        if detected != expected:
            raise InvalidDocumentContentError(
                "The image bytes do not match the declared image type"
            )
