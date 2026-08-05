from __future__ import annotations

from app.analysis.application.internal.outboundservices.document_text_extractor import (
    DocumentTextExtractor,
)
from app.analysis.application.internal.outboundservices.ollama_vision_extraction_client import (
    OllamaVisionExtractionClient,
)
from app.analysis.domain.exceptions import DocumentContentExtractionError
from app.analysis.domain.model.valueobjects.json_types import JsonContainer, JsonValue
from app.analysis.infrastructure.text_extraction.json_document_text_extractor import (
    JsonDocumentTextExtractor,
)
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType

_MAX_EXTRACTED_CHARACTERS = 200_000


class MultiFormatDocumentTextExtractor(DocumentTextExtractor):
    """Turns supported files into a bounded JSON-like representation for the AI."""

    def __init__(self, vision_client: OllamaVisionExtractionClient) -> None:
        self._json_extractor = JsonDocumentTextExtractor()
        self._vision_client = vision_client

    async def extract_content(
        self, content: bytes, mime_type: str, original_filename: str
    ) -> JsonContainer:
        normalized_mime_type = DocumentMimeType(mime_type).value

        if normalized_mime_type == DocumentMimeType.JSON:
            extracted = await self._json_extractor.extract_content(
                content, normalized_mime_type, original_filename
            )
        elif normalized_mime_type in {DocumentMimeType.PNG, DocumentMimeType.JPEG}:
            extracted = await self._extract_image(
                content, normalized_mime_type, original_filename
            )
        else:  # pragma: no cover - DocumentMimeType rejects this first
            raise DocumentContentExtractionError(
                f"Unsupported document type for {original_filename}"
            )

        if self._character_count(extracted) > _MAX_EXTRACTED_CHARACTERS:
            raise DocumentContentExtractionError(
                f"Unable to analyze {original_filename}: extracted content exceeds "
                f"the {_MAX_EXTRACTED_CHARACTERS}-character safety limit"
            )
        return extracted

    async def _extract_image(
        self, content: bytes, mime_type: str, original_filename: str
    ) -> JsonContainer:
        result = await self._vision_client.extract(
            image_content=content,
            mime_type=mime_type,
            reference_label=original_filename,
        )
        return result.to_document_payload()

    @classmethod
    def _character_count(cls, value: JsonValue) -> int:
        if isinstance(value, str):
            return len(value)
        if isinstance(value, list):
            return sum(cls._character_count(item) for item in value)
        if isinstance(value, dict):
            return sum(
                len(key) + cls._character_count(item) for key, item in value.items()
            )
        return 0
