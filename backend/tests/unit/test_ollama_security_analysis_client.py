import json

import pytest

from app.analysis.domain.exceptions import (
    AnalysisModelInvalidResponseError,
    AnalysisModelTimeoutError,
    AnalysisModelUnavailableError,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import AnalysisConfidence
from app.analysis.domain.model.valueobjects.analysis_finding_severity import (
    AnalysisFindingSeverity,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import AnalysisFindingType
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.analyzed_content_type import AnalyzedContentType
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel
from app.analysis.domain.model.valueobjects.security_evaluation_context import (
    SecurityEvaluationContext,
)
from app.analysis.infrastructure.ollama.ollama_security_analysis_client_impl import (
    OllamaSecurityAnalysisClientImpl,
)

TRANSPORT_MODULE = "app.shared.infrastructure.ollama.ollama_chat_transport"


def valid_payload() -> dict[str, object]:
    return {
        "risk_level": "high",
        "secrets_risk": "high",
        "personal_data_risk": "medium",
        "confidence": "high",
        "tampering_suspected": False,
        "data_categories": ["api_key"],
        "estimated_subjects": "1-5",
        "summary": "Rotate the exposed synthetic credential.",
        "rationale": "Finding f1 at the supplied JSONPath drives the secrets track.",
    }


def context() -> SecurityEvaluationContext:
    return SecurityEvaluationContext(
        content_type=AnalyzedContentType.DOCUMENT,
        reference_label="a***@example.com-export.json",
        approximate_size=200,
        estimated_subjects=EstimatedSubjects.ZERO,
        truncated=False,
        structure={
            "top_keys": ["api_key", "contacto ana.gomez@example.com"],
            "safe_sample": ['$.api_key="[REDACTED_API_KEY]"'],
        },
    )


def masked_finding() -> AnalysisFinding:
    return AnalysisFinding(
        finding_id="f1",
        finding_type=AnalysisFindingType.API_KEY,
        severity=AnalysisFindingSeverity.HIGH,
        title="API key detected",
        description="Safe description",
        json_path="$.api_key",
        evidence="sk-l************************f5Ja",
        detection_method="recognized_credential_pattern",
        confidence=AnalysisConfidence.HIGH,
        data_category="api_key",
    )


def client() -> OllamaSecurityAnalysisClientImpl:
    return OllamaSecurityAnalysisClientImpl("http://localhost:11434", "llama3.2:3b", 1, 2048, 300)


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._body


def test_validates_full_structured_contract() -> None:
    interpretation = OllamaAnalysisInterpretation.from_payload(valid_payload())
    assert interpretation.risk_level == AnalysisRiskLevel.HIGH
    assert interpretation.secrets_risk == SecretsRiskLevel.HIGH


def test_rejects_low_risk_model_text_that_claims_sensitive_data() -> None:
    payload = valid_payload()
    payload.update(
        {
            "risk_level": "low",
            "secrets_risk": "none",
            "personal_data_risk": "low",
            "data_categories": [],
            "summary": "Document contains masked sensitive data.",
            "rationale": "A personal identifier is present.",
        }
    )
    interpretation = OllamaAnalysisInterpretation.from_payload(payload)

    with pytest.raises(ValueError, match="low-risk"):
        client()._validate_against_supplied_findings(interpretation, [])


def test_rejects_model_references_to_findings_that_were_not_supplied() -> None:
    payload = valid_payload()
    interpretation = OllamaAnalysisInterpretation.from_payload(payload)

    with pytest.raises(ValueError, match="not supplied"):
        client()._validate_against_supplied_findings(interpretation, [])


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.pop("summary"),
        lambda payload: payload.update({"risk_level": "safe"}),
        lambda payload: payload.update({"summary": ""}),
        lambda payload: payload.update({"tampering_suspected": "false"}),
        lambda payload: payload.update({"extra": "not allowed"}),
    ],
)
def test_rejects_invalid_contract(mutation) -> None:
    payload = valid_payload()
    mutation(payload)
    with pytest.raises(ValueError):
        OllamaAnalysisInterpretation.from_payload(payload)


def test_rejects_sensitive_values_in_model_text() -> None:
    payload = valid_payload()
    payload["summary"] = "Contact ana.gomez@example.com immediately."
    with pytest.raises(ValueError, match="email"):
        OllamaAnalysisInterpretation.from_payload(payload)


def test_model_cannot_return_a_risk_below_its_own_tracks() -> None:
    payload = valid_payload()
    payload["risk_level"] = "low"
    with pytest.raises(ValueError, match="lower"):
        OllamaAnalysisInterpretation.from_payload(payload)


def test_prompt_masks_keys_filenames_and_paths_before_leaving() -> None:
    prompt = client()._build_user_prompt(context(), [masked_finding()])

    assert "sk-l************************f5Ja" in prompt
    assert "[REDACTED_API_KEY]" in prompt
    assert "sk-live51QpLd8Rt6VbNc1Zk9WsYh3Ge7Uf5Ja" not in prompt
    # A JSON key and a filename can carry an identity just like a value can.
    assert "ana.gomez@example.com" not in prompt
    assert "a***@example.com" in prompt


@pytest.mark.asyncio
async def test_timeout_raises_specific_exception(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", timeout)
    with pytest.raises(AnalysisModelTimeoutError):
        await client().evaluate(context=context(), findings=[masked_finding()])


@pytest.mark.asyncio
async def test_non_json_response_raises_specific_exception(monkeypatch) -> None:
    body = json.dumps({"message": {"content": "not-json"}}).encode()
    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", lambda *a, **k: _Response(body))
    with pytest.raises(AnalysisModelInvalidResponseError):
        await client().evaluate(context=context(), findings=[masked_finding()])


@pytest.mark.asyncio
async def test_unreachable_ollama_raises_unavailable(monkeypatch) -> None:
    def unreachable(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", unreachable)
    with pytest.raises(AnalysisModelUnavailableError):
        await client().evaluate(context=context(), findings=[masked_finding()])


@pytest.mark.asyncio
async def test_valid_response_is_parsed(monkeypatch) -> None:
    body = json.dumps({"message": {"content": json.dumps(valid_payload())}}).encode()
    monkeypatch.setattr(f"{TRANSPORT_MODULE}.urlopen", lambda *a, **k: _Response(body))

    interpretation = await client().evaluate(context=context(), findings=[masked_finding()])

    assert interpretation.risk_level == AnalysisRiskLevel.HIGH
