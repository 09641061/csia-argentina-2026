from typing import Protocol

from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis


class DocumentAnalysisRepository(Protocol):
    async def save(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        ...

    async def find_by_document_id(self, document_id: int) -> DocumentAnalysis | None:
        ...

    async def list(self, page: int, page_size: int) -> tuple[list[DocumentAnalysis], int]:
        ...

