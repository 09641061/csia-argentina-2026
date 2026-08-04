from typing import Protocol

from app.analysis.domain.model.valueobjects.source_document_reference import SourceDocumentReference


class DocumentSourceService(Protocol):
    async def get_document_reference(self, document_id: int) -> SourceDocumentReference | None:
        ...

