from app.analysis.domain.model.commands.analyze_document_command import AnalyzeDocumentCommand
from app.analysis.domain.model.commands.analyze_prompt_command import AnalyzePromptCommand
from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis
from app.analysis.domain.model.valueobjects.analysis_finding_type import AnalysisFindingType
from app.analysis.domain.services.security_analysis_command_service import (
    SecurityAnalysisCommandService,
)
from app.analysis.domain.services.security_analysis_query_service import (
    SecurityAnalysisQueryService,
)
from app.analysis.domain.model.queries.get_analysis_by_id_query import GetAnalysisByIdQuery
from app.decision.application.internal.outboundservices.content_review_service import (
    ContentReviewService,
)
from app.decision.domain.model.valueobjects.masked_finding_summary import MaskedFindingSummary
from app.decision.domain.model.valueobjects.reviewed_content_assessment import (
    ReviewedContentAssessment,
)


class ContentReviewServiceImpl(ContentReviewService):
    """
    Runs an Analysis execution and translates it into a decision-level assessment.

    An analysis error is not propagated as an exception: it is turned into a
    non-completed assessment, so the policy sees an unverified content and
    blocks it. That is what keeps the flow fail-closed end to end.
    """

    def __init__(
        self,
        analysis_command_service: SecurityAnalysisCommandService,
        analysis_query_service: SecurityAnalysisQueryService,
    ) -> None:
        self._analysis_command_service = analysis_command_service
        self._analysis_query_service = analysis_query_service

    async def review_prompt(self, prompt: str) -> ReviewedContentAssessment:
        try:
            analysis = await self._analysis_command_service.handle_analyze_prompt(
                AnalyzePromptCommand(prompt=prompt)
            )
        except Exception as error:  # noqa: BLE001 - an unverified prompt must block, not crash
            return await self._failed_assessment("prompt", "Consulta escrita", error)
        return self._to_assessment(analysis, "prompt")

    async def review_document(self, document_id: int) -> ReviewedContentAssessment:
        try:
            analysis = await self._analysis_command_service.handle_analyze_document(
                AnalyzeDocumentCommand(document_id=document_id)
            )
        except Exception as error:  # noqa: BLE001 - an unverified document must block, not crash
            return await self._failed_assessment("document", "Documento adjunto", error)
        return self._to_assessment(analysis, "document")

    async def _failed_assessment(
        self,
        origin: str,
        fallback_reference: str,
        error: Exception,
    ) -> ReviewedContentAssessment:
        analysis_id = getattr(self._analysis_command_service, "last_analysis_id", 0) or 0
        stored = None
        if analysis_id > 0:
            stored = await self._analysis_query_service.handle_get_analysis_by_id(
                GetAnalysisByIdQuery(analysis_id=analysis_id)
            )
        if stored is not None:
            return self._to_assessment(stored, origin)
        return ReviewedContentAssessment(
            analysis_id=analysis_id or 1,
            origin=origin,
            reference=fallback_reference,
            completed=False,
            risk_level=None,
            tampering_suspected=False,
            has_confirmed_sensitive_findings=False,
            has_prompt_injection=False,
            error_message=str(error) or "La revisión de seguridad no pudo completarse.",
        )

    def _to_assessment(
        self,
        analysis: SecurityAnalysis,
        origin: str,
    ) -> ReviewedContentAssessment:
        return ReviewedContentAssessment(
            analysis_id=analysis.id or 1,
            origin=origin,
            reference=analysis.content_reference,
            completed=analysis.is_completed,
            risk_level=analysis.risk_level.value if analysis.risk_level else None,
            tampering_suspected=analysis.tampering_suspected,
            has_confirmed_sensitive_findings=analysis.has_confirmed_sensitive_findings,
            has_prompt_injection=any(
                finding.finding_type == AnalysisFindingType.PROMPT_INJECTION
                for finding in analysis.findings
            ),
            data_categories=tuple(analysis.data_categories),
            findings=tuple(
                MaskedFindingSummary(
                    origin=origin,
                    finding_type=finding.finding_type.value,
                    severity=finding.severity.value,
                    title=finding.title,
                    location=finding.json_path,
                    masked_evidence=finding.masked_evidence,
                    occurrences=finding.occurrences,
                    is_placeholder=finding.is_placeholder,
                )
                for finding in analysis.findings
            ),
            error_message=analysis.error_message,
        )
