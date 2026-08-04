import json

import pytest

from app.analysis.domain.exceptions import (
    AnalysisModelInvalidResponseError,
    AnalysisModelTimeoutError,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_finding_severity import (
    AnalysisFindingSeverity,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.document_structure_summary import (
    DocumentStructureSummary,
)
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel
from app.analysis.domain.model.valueobjects.source_document_reference import (
    SourceDocumentReference,
)
from app.analysis.infrastructure.ollama.ollama_analysis_client_impl import (
    OllamaAnalysisClientImpl,
)


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


def source() -> SourceDocumentReference:
    return SourceDocumentReference(
        1, "fixture.json", "application/json", "https://example.invalid/file", 200
    )


def structure() -> DocumentStructureSummary:
    return DocumentStructureSummary(
        root_type="object",
        approximate_size_bytes=200,
        object_count=2,
        array_count=0,
        scalar_count=2,
        record_count=0,
        top_keys=("api_key",),
        finding_counts=(("api_key", 1),),
        data_categories=("api_key",),
        estimated_subjects=EstimatedSubjects.ZERO,
        safe_sample=('$.api_key="[REDACTED_API_KEY]"',),
        truncated=False,
        prompt_injection_paths=(),
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


def client() -> OllamaAnalysisClientImpl:
    return OllamaAnalysisClientImpl(
        "http://localhost:11434", "llama3.2:3b", 1, 2048, 300
    )


def test_validates_full_structured_contract() -> None:
    interpretation = OllamaAnalysisInterpretation.from_payload(valid_payload())
    assert interpretation.risk_level == AnalysisRiskLevel.HIGH
    assert interpretation.secrets_risk == SecretsRiskLevel.HIGH


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


def test_prompt_contains_only_masked_context() -> None:
    prompt = client()._build_user_prompt(source(), structure(), [masked_finding()])
    assert "sk-l************************f5Ja" in prompt
    assert "[REDACTED_API_KEY]" in prompt
    assert "sk-live51QpLd8Rt6VbNc1Zk9WsYh3Ge7Uf5Ja" not in prompt


def test_timeout_raises_specific_exception(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr(
        "app.analysis.infrastructure.ollama.ollama_analysis_client_impl.urlopen",
        timeout,
    )
    with pytest.raises(AnalysisModelTimeoutError):
        client()._generate(source(), structure(), [masked_finding()])


def test_non_json_response_raises_specific_exception(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            return json.dumps({"message": {"content": "not-json"}}).encode()

    monkeypatch.setattr(
        "app.analysis.infrastructure.ollama.ollama_analysis_client_impl.urlopen",
        lambda *args, **kwargs: Response(),
    )
    with pytest.raises(AnalysisModelInvalidResponseError):
        client()._generate(source(), structure(), [masked_finding()])
