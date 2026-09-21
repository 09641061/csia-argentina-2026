from typing import Protocol

from app.analysis.domain.model.valueobjects.json_types import JsonContainer


class DocumentTextExtractor(Protocol):
    async def extract_content(
        self, content: bytes, mime_type: str, original_filename: str
    ) -> JsonContainer: ...
