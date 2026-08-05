from dataclasses import dataclass

from app.decision.domain.model.entities.secure_interaction import SecureInteraction
from app.decision.domain.model.valueobjects.assistant_answer import AssistantAnswer


@dataclass(frozen=True, slots=True)
class SecureQueryResult:
    """Authorized query outcome returned by the Decision application service."""

    interaction: SecureInteraction
    answer: AssistantAnswer | None = None

    def __post_init__(self) -> None:
        if self.interaction.decision.value == "blocked" and self.answer is not None:
            raise ValueError("A blocked secure query cannot contain an answer")
