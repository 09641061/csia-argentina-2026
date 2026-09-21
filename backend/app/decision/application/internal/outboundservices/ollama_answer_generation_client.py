from typing import Protocol

from app.decision.domain.model.valueobjects.assistant_answer import AssistantAnswer
from app.decision.domain.model.valueobjects.generation_authorization import (
    GenerationAuthorization,
)


class OllamaAnswerGenerationClient(Protocol):
    """
    Use 2 of Ollama: answering an already allowed query.

    Completely separate from the security evaluator: its own system prompt, its
    own timeout, its own contract, and an authorization argument it refuses to
    work without.
    """

    @property
    def model_name(self) -> str: ...

    async def generate(
        self,
        *,
        authorization: GenerationAuthorization,
        prompt: str,
        allowed_document: dict[str, object] | list[object] | None = None,
        document_reference: str | None = None,
    ) -> AssistantAnswer: ...
