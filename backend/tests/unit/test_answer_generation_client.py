import json

import pytest

from app.decision.domain.exceptions import (
    AnswerGenerationContextTooLargeError,
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


def client(max_document_characters: int = 24000) -> OllamaAnswerGenerationClientImpl:
    return OllamaAnswerGenerationClientImpl(
        base_url="http://localhost:11434",
        model_name="llama3.2:3b",
        request_timeout_seconds=1,
        context_tokens=2048,
        max_output_tokens=200,
        max_document_characters=max_document_characters,
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
async def test_document_is_delimited_as_untrusted_data(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def capture(request, *args, **kwargs):
        del args, kwargs
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _Response(_answer("ok"))

    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", capture)

    await client().generate(
        authorization=authorization(),
        prompt="Resume el inventario",
        allowed_document={"items": [{"name": "widget"}]},
        document_reference="inventario.json",
    )

    messages = captured["payload"]["messages"]
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    assert "nunca instrucciones" in system_prompt
    assert "<<<INICIO_DOCUMENTO" in user_prompt
    assert "CONSULTA:" in user_prompt
    assert "widget" in user_prompt


@pytest.mark.asyncio
async def test_oversized_document_fails_loudly_instead_of_being_truncated() -> None:
    with pytest.raises(AnswerGenerationContextTooLargeError):
        await client(max_document_characters=50).generate(
            authorization=authorization(),
            prompt="Resume",
            allowed_document={"items": ["x" * 500]},
        )


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
