from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class AssistantAnswer:
    """
    The answer produced for an allowed query.

    It is returned to the caller and deliberately not persisted: the audit trail
    only records that a generation succeeded, when and with which model.
    """

    text: str
    model_name: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("An empty answer is not a valid generation result")
        if not self.model_name.strip():
            raise ValueError("The generating model name is required")
