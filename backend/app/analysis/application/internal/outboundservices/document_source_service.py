from typing import Protocol

from app.analysis.domain.model.valueobjects.analyzed_document_source import (
    AnalyzedDocumentSource,
)


class DocumentSourceService(Protocol):
    """
    Anti-corruption contract towards Documents.

    Analysis asks for safe metadata and for the bytes; it never learns where or
    how the document is stored.
    """

    async def get_document_source(self, document_id: int) -> AnalyzedDocumentSource | None: ...

    async def read_document_content(self, document_id: int) -> bytes: ...
