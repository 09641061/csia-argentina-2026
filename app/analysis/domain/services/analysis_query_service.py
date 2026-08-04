from typing import Protocol

from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis
from app.analysis.domain.model.queries.get_document_analysis_by_document_id_query import (
    GetDocumentAnalysisByDocumentIdQuery,
)
from app.analysis.domain.model.queries.list_document_analyses_query import ListDocumentAnalysesQuery


class AnalysisQueryService(Protocol):
    async def handle_get_document_analysis_by_document_id(
        self,
        query: GetDocumentAnalysisByDocumentIdQuery,
    ) -> DocumentAnalysis | None:
        ...

    async def handle_list_document_analyses(
        self,
        query: ListDocumentAnalysesQuery,
    ) -> tuple[list[DocumentAnalysis], int]:
        ...
