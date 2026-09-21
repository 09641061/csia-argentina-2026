from typing import Protocol

from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis
from app.analysis.domain.model.queries.get_analysis_by_id_query import (
    GetAnalysisByIdQuery,
)
from app.analysis.domain.model.queries.get_latest_analysis_by_document_id_query import (
    GetLatestAnalysisByDocumentIdQuery,
)
from app.analysis.domain.model.queries.list_analyses_query import ListAnalysesQuery


class SecurityAnalysisQueryService(Protocol):
    async def handle_get_analysis_by_id(
        self,
        query: GetAnalysisByIdQuery,
    ) -> SecurityAnalysis | None: ...

    async def handle_get_latest_analysis_by_document_id(
        self,
        query: GetLatestAnalysisByDocumentIdQuery,
    ) -> SecurityAnalysis | None: ...

    async def handle_list_analyses(
        self,
        query: ListAnalysesQuery,
    ) -> tuple[list[SecurityAnalysis], int]: ...
