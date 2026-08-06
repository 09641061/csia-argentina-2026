import pytest

from app.decision.domain.model.valueobjects.decision_reason_code import (
    DecisionReasonCode,
)
from app.decision.domain.model.valueobjects.generation_authorization import (
    GenerationAuthorization,
)
from app.decision.domain.model.valueobjects.reviewed_content_assessment import (
    ReviewedContentAssessment,
)
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.decision.domain.policies.secure_query_decision_policy import (
    SecureQueryDecisionPolicy,
)


def assessment(
    origin: str,
    *,
    completed: bool = True,
    risk_level: str | None = "low",
    tampering: bool = False,
    confirmed: bool = False,
    injection: bool = False,
) -> ReviewedContentAssessment:
    return ReviewedContentAssessment(
        analysis_id=1 if origin == "prompt" else 2,
        origin=origin,
        reference="fixture",
        completed=completed,
        risk_level=risk_level,
        tampering_suspected=tampering,
        has_confirmed_sensitive_findings=confirmed,
        has_prompt_injection=injection,
    )


def test_clean_prompt_is_allowed() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=assessment("prompt"), document_assessment=None
    )
    assert outcome.decision == SecurityDecision.ALLOWED
    assert outcome.reason_code == DecisionReasonCode.CONTENT_IS_SAFE


def test_clean_prompt_with_clean_document_is_allowed() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=assessment("prompt"), document_assessment=assessment("document")
    )
    assert outcome.decision == SecurityDecision.ALLOWED


def test_sensitive_document_blocks_the_whole_query() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=assessment("prompt"),
        document_assessment=assessment("document", risk_level="high", confirmed=True),
    )
    assert outcome.decision == SecurityDecision.BLOCKED
    assert outcome.reason_code == DecisionReasonCode.DOCUMENT_CONTAINS_SENSITIVE_DATA
    assert outcome.risk_level == "high"


def test_sensitive_prompt_blocks_even_with_a_clean_document() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=assessment("prompt", risk_level="high", confirmed=True),
        document_assessment=assessment("document"),
    )
    assert outcome.decision == SecurityDecision.BLOCKED
    assert outcome.reason_code == DecisionReasonCode.PROMPT_CONTAINS_SENSITIVE_DATA


def test_prompt_injection_blocks_before_any_other_reason() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=assessment("prompt", risk_level="high", injection=True, tampering=True),
        document_assessment=None,
    )
    assert outcome.reason_code == DecisionReasonCode.PROMPT_INJECTION_DETECTED


def test_failed_review_blocks_and_is_never_read_as_low_risk() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=assessment("prompt", completed=False, risk_level=None),
        document_assessment=None,
    )
    assert outcome.decision == SecurityDecision.BLOCKED
    assert outcome.reason_code == DecisionReasonCode.PROMPT_REVIEW_FAILED
    assert outcome.risk_level is None


def test_medium_risk_without_confirmed_findings_still_blocks() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=assessment("prompt", risk_level="medium"),
        document_assessment=None,
    )
    assert outcome.decision == SecurityDecision.BLOCKED


def test_nothing_submitted_is_blocked() -> None:
    outcome = SecureQueryDecisionPolicy().evaluate(
        prompt_assessment=None, document_assessment=None
    )
    assert outcome.decision == SecurityDecision.BLOCKED
    assert outcome.reason_code == DecisionReasonCode.NO_CONTENT_SUBMITTED


def test_generation_authorization_cannot_exist_for_a_blocked_decision() -> None:
    with pytest.raises(ValueError, match="allowed decision"):
        GenerationAuthorization(decision=SecurityDecision.BLOCKED, prompt_analysis_id=1)


def test_generation_authorization_requires_a_prompt_analysis() -> None:
    with pytest.raises(ValueError, match="prompt analysis"):
        GenerationAuthorization(decision=SecurityDecision.ALLOWED, prompt_analysis_id=0)
