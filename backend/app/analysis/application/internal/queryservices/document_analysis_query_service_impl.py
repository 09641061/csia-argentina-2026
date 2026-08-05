from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis
from app.analysis.domain.model.queries.get_document_analysis_by_document_id_query import (
    GetDocumentAnalysisByDocumentIdQuery,
)
from app.analysis.domain.model.queries.get_document_analysis_by_id_query import (
    GetDocumentAnalysisByIdQuery,
)
from app.analysis.domain.model.queries.list_document_analyses_query import (
    ListDocumentAnalysesQuery,
)
from app.analysis.domain.repositories.document_analysis_repository import (
    DocumentAnalysisRepository,
)
from app.analysis.domain.services.analysis_query_service import AnalysisQueryService


class DocumentAnalysisQueryServiceImpl(AnalysisQueryService):
    def __init__(self, analysis_repository: DocumentAnalysisRepository) -> None:
        self._analysis_repository = analysis_repository

    async def handle_get_document_analysis_by_document_id(
        self,
        query: GetDocumentAnalysisByDocumentIdQuery,
    ) -> DocumentAnalysis | None:
        return await self._analysis_repository.find_by_document_id(query.document_id)

    async def handle_list_document_analyses(
        self,
        query: ListDocumentAnalysesQuery,
    ) -> tuple[list[DocumentAnalysis], int]:
        return await self._analysis_repository.list(query.page, query.page_size)

    async def handle_get_document_analysis_by_id(
        self,
        query: GetDocumentAnalysisByIdQuery,
    ) -> DocumentAnalysis | None:
        return await self._analysis_repository.find_by_id(query.analysis_id)
