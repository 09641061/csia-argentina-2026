from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.decision.domain.model.valueobjects.decision_reason_code import DecisionReasonCode
from app.decision.domain.model.valueobjects.generation_authorization import (
    GenerationAuthorization,
)
from app.decision.domain.model.valueobjects.generation_status import GenerationStatus
from app.decision.domain.model.valueobjects.interaction_content_type import (
    InteractionContentType,
)
from app.decision.domain.model.valueobjects.masked_finding_summary import MaskedFindingSummary
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision


@dataclass(slots=True)
class SecureInteraction:
    """
    One single secure query: what was submitted, what was decided and whether an
    answer could be produced.

    This is not a conversation. There is no message list, no memory and no
    stored answer text: the answer is returned once to the caller, and the audit
    trail keeps only that a generation succeeded, when, and with which model.
    """

    id: int | None
    content_type: InteractionContentType
    decision: SecurityDecision
    reason_code: DecisionReasonCode
    reason: str
    content_reference: str
    risk_level: str | None = None
    prompt_analysis_id: int | None = None
    document_analysis_id: int | None = None
    document_id: int | None = None
    masked_findings: list[MaskedFindingSummary] = field(default_factory=list)
    data_categories: list[str] = field(default_factory=list)
    generation_status: GenerationStatus = GenerationStatus.NOT_REQUESTED
    generation_model: str | None = None
    generation_error: str | None = None
    generated_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.id is not None and self.id <= 0:
            raise ValueError("Interaction ID must be a positive number")
        if not self.reason.strip():
            raise ValueError("A decision reason is required")
        if not self.content_reference.strip():
            raise ValueError("A safe content reference is required")
        if self.decision == SecurityDecision.BLOCKED and self.generation_status in {
            GenerationStatus.SUCCEEDED,
            GenerationStatus.FAILED,
        }:
            raise ValueError("A blocked interaction can never reach the answer generator")

    @classmethod
    def record(
        cls,
        *,
        content_type: InteractionContentType,
        decision: SecurityDecision,
        reason_code: DecisionReasonCode,
        reason: str,
        content_reference: str,
        risk_level: str | None,
        prompt_analysis_id: int | None,
        document_analysis_id: int | None,
        document_id: int | None,
        masked_findings: list[MaskedFindingSummary],
        data_categories: list[str],
        answer_expected: bool,
    ) -> "SecureInteraction":
        if decision == SecurityDecision.BLOCKED:
            generation_status = GenerationStatus.SKIPPED
        elif answer_expected:
            generation_status = GenerationStatus.NOT_REQUESTED
        else:
            generation_status = GenerationStatus.NOT_REQUESTED

        return cls(
            id=None,
            content_type=content_type,
            decision=decision,
            reason_code=reason_code,
            reason=reason,
            content_reference=content_reference,
            risk_level=risk_level,
            prompt_analysis_id=prompt_analysis_id,
            document_analysis_id=document_analysis_id,
            document_id=document_id,
            masked_findings=list(masked_findings),
            data_categories=sorted(set(data_categories)),
            generation_status=generation_status,
        )

    def record_successful_generation(
        self,
        authorization: GenerationAuthorization,
        model_name: str,
    ) -> None:
        self._assert_generation_is_authorized(authorization)
        self.generation_status = GenerationStatus.SUCCEEDED
        self.generation_model = model_name
        self.generation_error = None
        self.generated_at = datetime.now(UTC)

    def record_failed_generation(
        self,
        authorization: GenerationAuthorization,
        model_name: str,
        safe_error_message: str,
    ) -> None:
        self._assert_generation_is_authorized(authorization)
        if not safe_error_message.strip():
            raise ValueError("A safe generation error message is required")
        self.generation_status = GenerationStatus.FAILED
        self.generation_model = model_name
        self.generation_error = safe_error_message.strip()
        self.generated_at = None

    def _assert_generation_is_authorized(self, authorization: GenerationAuthorization) -> None:
        if self.decision != SecurityDecision.ALLOWED:
            raise ValueError("Only an allowed interaction can record a generation attempt")
        if authorization.decision != SecurityDecision.ALLOWED:
            raise ValueError("The generation authorization is not valid")

    @property
    def answer_was_generated(self) -> bool:
        return self.generation_status == GenerationStatus.SUCCEEDED
