from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ChatMessageResult:
    interaction_id: int
    decision: str
    reason: str
    document_id: int | None
    answer: str | None
    answer_model: str | None
    generated_at: datetime | None
    attachment_url: str | None = None

    def __post_init__(self) -> None:
        if self.interaction_id <= 0:
            raise ValueError("Interaction ID must be positive")
        if self.decision not in {"allowed", "blocked"}:
            raise ValueError("Chat decision must be allowed or blocked")
        if not self.reason.strip():
            raise ValueError("Chat decision reason is required")
        if self.decision == "blocked" and self.answer is not None:
            raise ValueError("A blocked chat message cannot contain an answer")
