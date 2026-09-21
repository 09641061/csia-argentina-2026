from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SendChatMessageCommand:
    prompt: str
    requested_by: str = "system"
    attachment_payload: dict[str, Any] | list[Any] | None = None
    attachment_name: str | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Message is required")
        if not self.requested_by.strip():
            raise ValueError("Authenticated user is required")
