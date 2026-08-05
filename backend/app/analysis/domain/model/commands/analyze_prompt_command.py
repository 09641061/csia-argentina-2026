from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalyzePromptCommand:
    prompt: str

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Prompt text is required")
