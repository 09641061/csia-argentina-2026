from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SendChatMessageCommand:
    prompt: str

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Message is required")
