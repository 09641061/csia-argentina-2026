from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SubmitSecureQueryCommand:
    """
    A single text query submitted to the secure assistant.
    """

    prompt: str | None = None
    requested_by: str = "system"
    attachment_payload: dict[str, Any] | list[Any] | None = None
    attachment_name: str | None = None

    def __post_init__(self) -> None:
        if not self.requested_by.strip():
            raise ValueError("Authenticated user is required")
        has_prompt = bool((self.prompt or "").strip())
        if not has_prompt:
            raise ValueError("Se necesita una consulta de texto.")

    @property
    def has_prompt(self) -> bool:
        return bool((self.prompt or "").strip())
