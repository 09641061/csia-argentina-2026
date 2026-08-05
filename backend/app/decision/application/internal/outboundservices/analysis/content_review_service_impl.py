from app.analysis.interfaces.acl.analysis_context_facade import AnalysisContextFacade
from app.decision.application.internal.outboundservices.content_review_service import (
    ContentReviewService,
)
from app.decision.domain.model.valueobjects.masked_finding_summary import MaskedFindingSummary
from app.decision.domain.model.valueobjects.reviewed_content_assessment import (
    ReviewedContentAssessment,
)


class ContentReviewServiceImpl(ContentReviewService):
    """Translate the public Analysis ACL contract into Decision concepts."""

    def __init__(self, analysis_facade: AnalysisContextFacade) -> None:
        self._analysis_facade = analysis_facade

    async def review_prompt(self, prompt: str) -> ReviewedContentAssessment:
        return self._to_assessment(await self._analysis_facade.review_prompt(prompt))

    async def review_document(self, document_id: int) -> ReviewedContentAssessment:
        return self._to_assessment(await self._analysis_facade.review_document(document_id))

    @staticmethod
    def _to_assessment(payload: dict[str, object | None]) -> ReviewedContentAssessment:
        raw_findings = payload.get("findings")
        findings = raw_findings if isinstance(raw_findings, list) else []
        raw_categories = payload.get("data_categories")
        categories = raw_categories if isinstance(raw_categories, list) else []
        return ReviewedContentAssessment(
            analysis_id=int(payload["analysis_id"] or 0),
            origin=str(payload["origin"]),
            reference=str(payload["reference"]),
            completed=bool(payload["completed"]),
            risk_level=str(payload["risk_level"]) if payload["risk_level"] else None,
            tampering_suspected=bool(payload["tampering_suspected"]),
            has_confirmed_sensitive_findings=bool(
                payload["has_confirmed_sensitive_findings"]
            ),
            has_prompt_injection=bool(payload["has_prompt_injection"]),
            data_categories=tuple(str(category) for category in categories),
            findings=tuple(
                MaskedFindingSummary(
                    origin=str(finding["origin"]),
                    finding_type=str(finding["finding_type"]),
                    severity=str(finding["severity"]),
                    title=str(finding["title"]),
                    location=str(finding["location"]),
                    masked_evidence=str(finding["masked_evidence"]),
                    occurrences=int(finding["occurrences"]),
                    is_placeholder=bool(finding["is_placeholder"]),
                )
                for finding in findings
                if isinstance(finding, dict)
            ),
            error_message=(
                str(payload["error_message"]) if payload.get("error_message") else None
            ),
        )
