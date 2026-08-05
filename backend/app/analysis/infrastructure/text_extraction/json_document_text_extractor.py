from __future__ import annotations

import json

from app.analysis.application.internal.outboundservices.document_text_extractor import (
    DocumentTextExtractor,
)
from app.analysis.domain.exceptions import DocumentContentExtractionError
from app.analysis.domain.model.valueobjects.json_types import JsonContainer

JSON_MIME_TYPE = "application/json"


class JsonDocumentTextExtractor(DocumentTextExtractor):
    """
    Extracts analyzable text from JSON documents.

    JSON is the only supported document type. Anything that cannot be read is
    rejected instead of returning empty text, so an unreadable document never
    reaches the analysis as a low-risk result.
    """

    def extract_json(
        self, content: bytes, mime_type: str, original_filename: str
    ) -> JsonContainer:
        normalized_mime_type = mime_type.split(";", maxsplit=1)[0].strip().lower()

        if normalized_mime_type != JSON_MIME_TYPE:
            raise DocumentContentExtractionError(
                f"Unsupported document type for {original_filename}: {normalized_mime_type}. "
                f"Only {JSON_MIME_TYPE} can be analyzed"
            )

        try:
            parsed = json.loads(content.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise DocumentContentExtractionError(
                f"Unable to extract text from {original_filename}: content is not UTF-8 encoded"
            ) from error
        except (json.JSONDecodeError, RecursionError) as error:
            raise DocumentContentExtractionError(
                f"Unable to extract text from {original_filename}: content is not valid JSON"
            ) from error

        if not isinstance(parsed, (dict, list)):
            raise DocumentContentExtractionError(
                f"Unable to extract JSON from {original_filename}: root must be an object or array"
            )

        return parsed

    def extract_text(
        self, content: bytes, mime_type: str, original_filename: str
    ) -> str:
        """Compatibility helper for callers that still need a JSON rendering."""

        parsed = self.extract_json(content, mime_type, original_filename)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
