from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.decision.domain.model.valueobjects.security_decision import SecurityDecision


@dataclass(frozen=True, slots=True)
class SecureInteractionDecidedEvent:
    event_id: UUID = field(default_factory=uuid4)
    interaction_id: int = 0
    decision: SecurityDecision = SecurityDecision.BLOCKED
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.interaction_id <= 0:
            raise ValueError("Interaction ID must be a positive number")
