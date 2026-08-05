from __future__ import annotations

from dataclasses import dataclass

from app.decision.domain.model.valueobjects.decision_reason_code import DecisionReasonCode
from app.decision.domain.model.valueobjects.reviewed_content_assessment import (
    ReviewedContentAssessment,
)
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    decision: SecurityDecision
    reason_code: DecisionReasonCode
    reason: str
    risk_level: str | None


class SecureQueryDecisionPolicy:
    """
    The single place where ALLOWED and BLOCKED are decided.

    The policy is fail-closed by construction: it starts from BLOCKED and only
    returns ALLOWED when every submitted piece of content completed its review,
    came back with a low risk, showed no confirmed sensitive finding, no
    tampering and no prompt injection. An unfinished, failed or unverifiable
    review is a block, never a low risk.
    """

    def evaluate(
        self,
        *,
        prompt_assessment: ReviewedContentAssessment | None,
        document_assessment: ReviewedContentAssessment | None,
    ) -> DecisionOutcome:
        assessments = [item for item in (prompt_assessment, document_assessment) if item is not None]
        if not assessments:
            return DecisionOutcome(
                decision=SecurityDecision.BLOCKED,
                reason_code=DecisionReasonCode.NO_CONTENT_SUBMITTED,
                reason="No se recibió ninguna consulta ni documento para revisar.",
                risk_level=None,
            )

        risk_level = self._highest_risk(assessments)

        if prompt_assessment is not None and not prompt_assessment.completed:
            return DecisionOutcome(
                decision=SecurityDecision.BLOCKED,
                reason_code=DecisionReasonCode.PROMPT_REVIEW_FAILED,
                reason=(
                    "No fue posible verificar la consulta, por lo que no se envió al asistente."
                ),
                risk_level=risk_level,
            )
        if document_assessment is not None and not document_assessment.completed:
            return DecisionOutcome(
                decision=SecurityDecision.BLOCKED,
                reason_code=DecisionReasonCode.DOCUMENT_REVIEW_FAILED,
                reason=(
                    "No fue posible verificar el documento, por lo que no se envió al asistente."
                ),
                risk_level=risk_level,
            )

        if (prompt_assessment is not None and prompt_assessment.has_prompt_injection) or (
            document_assessment is not None and document_assessment.has_prompt_injection
        ):
            return DecisionOutcome(
                decision=SecurityDecision.BLOCKED,
                reason_code=DecisionReasonCode.PROMPT_INJECTION_DETECTED,
                reason=(
                    "Se detectó un intento de manipular las instrucciones del sistema."
                ),
                risk_level=risk_level,
            )

        if prompt_assessment is not None and not prompt_assessment.is_safe:
            return DecisionOutcome(
                decision=SecurityDecision.BLOCKED,
                reason_code=DecisionReasonCode.PROMPT_CONTAINS_SENSITIVE_DATA,
                reason="La consulta contiene información sensible.",
                risk_level=risk_level,
            )

        if document_assessment is not None and not document_assessment.is_safe:
            return DecisionOutcome(
                decision=SecurityDecision.BLOCKED,
                reason_code=DecisionReasonCode.DOCUMENT_CONTAINS_SENSITIVE_DATA,
                reason="El documento adjunto contiene información sensible.",
                risk_level=risk_level,
            )

        return DecisionOutcome(
            decision=SecurityDecision.ALLOWED,
            reason_code=DecisionReasonCode.CONTENT_IS_SAFE,
            reason="No se detectó información sensible en el contenido revisado.",
            risk_level=risk_level,
        )

    def _highest_risk(self, assessments: list[ReviewedContentAssessment]) -> str | None:
        levels = [item.risk_level for item in assessments if item.risk_level]
        if not levels:
            return None
        return max(levels, key=lambda level: _RISK_ORDER.get(level, 0))
