import json

import pytest

from app.decision.domain.exceptions import (
    AnswerGenerationEmptyError,
    AnswerGenerationTimeoutError,
    AnswerGenerationUnavailableError,
)
from app.decision.domain.model.valueobjects.generation_authorization import (
    GenerationAuthorization,
)
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.decision.infrastructure.ollama.ollama_answer_generation_client_impl import (
    OllamaAnswerGenerationClientImpl,
)

TRANSPORT_MODULE = "app.shared.infrastructure.ollama.ollama_chat_transport"


def client() -> OllamaAnswerGenerationClientImpl:
    return OllamaAnswerGenerationClientImpl(
        base_url="http://localhost:11434",
        model_name="llama3.2:3b",
        request_timeout_seconds=1,
        context_tokens=2048,
        max_output_tokens=200,
    )


def authorization() -> GenerationAuthorization:
    return GenerationAuthorization(decision=SecurityDecision.ALLOWED, prompt_analysis_id=1)


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._body


def _answer(text: str) -> bytes:
    return json.dumps({"message": {"content": text}}).encode()


@pytest.mark.asyncio
async def test_generates_an_answer_for_an_authorized_prompt(monkeypatch) -> None:
    monkeypatch.setattr(
        f"{TRANSPORT_MODULE}.urlopen", lambda *a, **k: _Response(_answer("Una respuesta."))
    )

    answer = await client().generate(authorization=authorization(), prompt="¿Qué es DDD?")

    assert answer.text == "Una respuesta."
    assert answer.model_name == "llama3.2:3b"


@pytest.mark.asyncio
async def test_generator_refuses_to_run_without_a_valid_authorization() -> None:
    class ForgedAuthorization:
        decision = SecurityDecision.BLOCKED

    with pytest.raises(ValueError, match="ALLOWED authorization"):
        await client().generate(authorization=ForgedAuthorization(), prompt="¿Qué es DDD?")


@pytest.mark.asyncio
async def test_timeout_is_reported_as_a_generation_timeout(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", timeout)
    with pytest.raises(AnswerGenerationTimeoutError):
        await client().generate(authorization=authorization(), prompt="Hola")


@pytest.mark.asyncio
async def test_unreachable_generator_is_reported_as_unavailable(monkeypatch) -> None:
    def unreachable(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", unreachable)
    with pytest.raises(AnswerGenerationUnavailableError):
        await client().generate(authorization=authorization(), prompt="Hola")


@pytest.mark.asyncio
async def test_empty_answer_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", lambda *a, **k: _Response(_answer("   ")))
    with pytest.raises(AnswerGenerationEmptyError):
        await client().generate(authorization=authorization(), prompt="Hola")
