from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.decision.domain.model.valueobjects.security_decision import SecurityDecision


@dataclass(frozen=True, slots=True)
class GenerationAuthorization:
    """
    Proof that the security review allowed this exact content.

    The answer generator refuses to run without one, and one cannot exist unless
    the decision is ALLOWED. That makes "a blocked query reaches the generator"
    unrepresentable rather than merely unlikely.
    """

    decision: SecurityDecision
    prompt_analysis_id: int
    document_analysis_id: int | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.decision != SecurityDecision.ALLOWED:
            raise ValueError("Generation can only be authorized for an allowed decision")
        if self.prompt_analysis_id <= 0:
            raise ValueError("An authorized generation requires a completed prompt analysis")
        if self.document_analysis_id is not None and self.document_analysis_id <= 0:
            raise ValueError("Document analysis identifier must be a positive number")
