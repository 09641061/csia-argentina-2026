from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis
from app.analysis.domain.model.queries.get_analysis_by_id_query import (
    GetAnalysisByIdQuery,
)
from app.analysis.domain.model.queries.get_latest_analysis_by_document_id_query import (
    GetLatestAnalysisByDocumentIdQuery,
)
from app.analysis.domain.model.queries.list_analyses_query import ListAnalysesQuery
from app.analysis.domain.repositories.security_analysis_repository import (
    SecurityAnalysisRepository,
)
from app.analysis.domain.services.security_analysis_query_service import (
    SecurityAnalysisQueryService,
)


class SecurityAnalysisQueryServiceImpl(SecurityAnalysisQueryService):
    def __init__(self, analysis_repository: SecurityAnalysisRepository) -> None:
        self._analysis_repository = analysis_repository

    async def handle_get_analysis_by_id(
        self,
        query: GetAnalysisByIdQuery,
    ) -> SecurityAnalysis | None:
        return await self._analysis_repository.find_by_id(query.analysis_id, query.requested_by)

    async def handle_get_latest_analysis_by_document_id(
        self,
        query: GetLatestAnalysisByDocumentIdQuery,
    ) -> SecurityAnalysis | None:
        return await self._analysis_repository.find_latest_by_document_id(query.document_id)

    async def handle_list_analyses(
        self,
        query: ListAnalysesQuery,
    ) -> tuple[list[SecurityAnalysis], int]:
        return await self._analysis_repository.list(query.requested_by, query.page, query.page_size)
