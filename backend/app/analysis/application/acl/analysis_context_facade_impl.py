from collections.abc import Awaitable, Callable

from app.analysis.domain.model.commands.analyze_document_command import AnalyzeDocumentCommand
from app.analysis.domain.model.commands.analyze_prompt_command import AnalyzePromptCommand
from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis
from app.analysis.domain.model.queries.get_analysis_by_id_query import GetAnalysisByIdQuery
from app.analysis.domain.services.security_analysis_command_service import (
    SecurityAnalysisCommandService,
)
from app.analysis.domain.services.security_analysis_query_service import SecurityAnalysisQueryService
from app.analysis.interfaces.acl.analysis_context_facade import AnalysisContextFacade


class AnalysisContextFacadeImpl(AnalysisContextFacade):
    def __init__(
        self,
        command_service: SecurityAnalysisCommandService,
        query_service: SecurityAnalysisQueryService,
    ) -> None:
        self._command_service = command_service
        self._query_service = query_service

    async def review_prompt(self, prompt: str) -> dict[str, object | None]:
        return await self._review(
            operation=lambda: self._command_service.handle_analyze_prompt(
                AnalyzePromptCommand(prompt=prompt)
            ),
            origin="prompt",
            fallback_reference="Consulta escrita",
        )

    async def review_document(self, document_id: int) -> dict[str, object | None]:
        return await self._review(
            operation=lambda: self._command_service.handle_analyze_document(
                AnalyzeDocumentCommand(document_id=document_id)
            ),
            origin="document",
            fallback_reference="Documento adjunto",
        )

    async def _review(
        self,
        *,
        operation: Callable[[], Awaitable[SecurityAnalysis]],
        origin: str,
        fallback_reference: str,
    ) -> dict[str, object | None]:
        try:
            analysis = await operation()
        except Exception as error:  # noqa: BLE001 - the ACL returns an explicit failed review
            analysis_id = getattr(self._command_service, "last_analysis_id", 0) or 0
            stored = None
            if analysis_id > 0:
                stored = await self._query_service.handle_get_analysis_by_id(
                    GetAnalysisByIdQuery(analysis_id=analysis_id)
                )
            if stored is not None:
                return self._to_payload(stored, origin)
            return {
                "analysis_id": analysis_id or 1,
                "origin": origin,
                "reference": fallback_reference,
                "completed": False,
                "risk_level": None,
                "tampering_suspected": False,
                "has_confirmed_sensitive_findings": False,
                "has_prompt_injection": False,
                "data_categories": [],
                "findings": [],
                "error_message": str(error) or "La revisión no pudo completarse.",
            }
        return self._to_payload(analysis, origin)

    @staticmethod
    def _to_payload(analysis: SecurityAnalysis, origin: str) -> dict[str, object | None]:
        return {
            "analysis_id": analysis.id or 1,
            "origin": origin,
            "reference": analysis.content_reference,
            "completed": analysis.is_completed,
            "risk_level": analysis.risk_level.value if analysis.risk_level else None,
            "tampering_suspected": analysis.tampering_suspected,
            "has_confirmed_sensitive_findings": analysis.has_confirmed_sensitive_findings,
            "has_prompt_injection": any(
                finding.finding_type.value == "prompt_injection" for finding in analysis.findings
            ),
            "data_categories": list(analysis.data_categories),
            "findings": [
                {
                    "origin": origin,
                    "finding_type": finding.finding_type.value,
                    "severity": finding.severity.value,
                    "title": finding.title,
                    "location": finding.json_path,
                    "masked_evidence": finding.masked_evidence,
                    "occurrences": finding.occurrences,
                    "is_placeholder": finding.is_placeholder,
                }
                for finding in analysis.findings
            ],
            "error_message": analysis.error_message,
        }
