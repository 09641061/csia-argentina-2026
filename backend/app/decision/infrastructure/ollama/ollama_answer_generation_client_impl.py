from __future__ import annotations

from pathlib import Path

from app.decision.application.internal.outboundservices.ollama_answer_generation_client import (
    OllamaAnswerGenerationClient,
)
from app.decision.domain.exceptions import (
    AnswerGenerationEmptyError,
    AnswerGenerationTimeoutError,
    AnswerGenerationUnavailableError,
)
from app.decision.domain.model.valueobjects.assistant_answer import AssistantAnswer
from app.decision.domain.model.valueobjects.generation_authorization import (
    GenerationAuthorization,
)
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.shared.infrastructure.ollama.ollama_chat_transport import (
    OllamaChatTransport,
    OllamaMalformedResponseError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


class OllamaAnswerGenerationClientImpl(OllamaAnswerGenerationClient):
    """
    Answers an allowed query with the local model.

    Generates an answer only for a previously authorized text query.
    """

    def __init__(
        self,
        base_url: str,
        model_name: str,
        request_timeout_seconds: int,
        context_tokens: int,
        max_output_tokens: int,
    ) -> None:
        if not model_name.strip():
            raise ValueError("Ollama generation model name is required")
        if (
            min(
                request_timeout_seconds,
                context_tokens,
                max_output_tokens,
            )
            <= 0
        ):
            raise ValueError("Ollama generation numeric settings must be positive")
        self._transport = OllamaChatTransport(base_url)
        self._model_name = model_name
        self._request_timeout_seconds = request_timeout_seconds
        self._context_tokens = context_tokens
        self._max_output_tokens = max_output_tokens
        self._system_prompt = self._load_system_prompt()

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate(
        self,
        *,
        authorization: GenerationAuthorization,
        prompt: str,
    ) -> AssistantAnswer:
        if authorization.decision != SecurityDecision.ALLOWED:
            raise ValueError("The answer generator requires a valid ALLOWED authorization")
        if not prompt.strip():
            raise ValueError("The answer generator requires a question")

        user_prompt = self._build_user_prompt(prompt)

        try:
            text = await self._transport.chat(
                model_name=self._model_name,
                system_prompt=self._system_prompt,
                user_prompt=user_prompt,
                timeout_seconds=self._request_timeout_seconds,
                options={
                    "num_ctx": self._context_tokens,
                    "num_predict": self._max_output_tokens,
                    "temperature": 0.2,
                },
                json_format=False,
            )
        except OllamaTimeoutError as error:
            raise AnswerGenerationTimeoutError(
                "El asistente local no respondió dentro del tiempo configurado."
            ) from error
        except (OllamaUnavailableError, OllamaMalformedResponseError) as error:
            raise AnswerGenerationUnavailableError(
                "El asistente local no está disponible en este momento."
            ) from error

        if not text.strip():
            raise AnswerGenerationEmptyError("El asistente local devolvió una respuesta vacía.")

        return AssistantAnswer(text=text.strip(), model_name=self._model_name)

    def _load_system_prompt(self) -> str:
        prompt_path = (
            Path(__file__).resolve().parents[3]
            / "shared"
            / "prompts"
            / "assistant_generation_system_prompt.md"
        )
        return prompt_path.read_text(encoding="utf-8").strip()

    def _build_user_prompt(
        self,
        prompt: str,
    ) -> str:
        return f"CONSULTA:\n{prompt.strip()}"
