from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalyzePromptCommand:
    prompt: str
    requested_by: str = "system"

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Prompt text is required")
        if not self.requested_by.strip():
            raise ValueError("Authenticated user is required")
