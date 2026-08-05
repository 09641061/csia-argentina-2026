import json

from app.analysis.application.internal.services.document_free_text_sensitive_data_detection_service import (
    DocumentFreeTextSensitiveDataDetectionService,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)
from app.analysis.infrastructure.ollama.ollama_sensitive_content_discovery_client_impl import (
    OllamaSensitiveContentDiscoveryClientImpl,
)


def test_applies_labeled_identity_rules_inside_extracted_word_text() -> None:
    findings = DocumentFreeTextSensitiveDataDetectionService().scan(
        {
            "format": "docx",
            "paragraphs": [{"paragraph": 1, "text": "DNI: 65432112"}],
        }
    )

    assert len(findings) == 1
    assert findings[0].finding_type == AnalysisFindingType.PERSONAL_ID
    assert findings[0].json_path == "$.paragraphs[0].text"
    assert findings[0].masked_evidence == "6*****12"


def test_discovery_contract_normalizes_categories_without_preserving_model_text() -> None:
    client = OllamaSensitiveContentDiscoveryClientImpl(
        base_url="http://localhost:11434",
        model_name="fake-discovery",
        request_timeout_seconds=1,
        context_tokens=1024,
        max_output_tokens=100,
        max_input_characters=1000,
    )

    result = client._parse(
        json.dumps(
            {
                "has_sensitive": True,
                "categories": [
                    "identity numbers",
                    "card data",
                    "account data",
                    "an unexpected model phrase",
                ],
            }
        )
    )

    assert result.contains_sensitive_data is True
    assert result.risk_level.value == "high"
    assert set(result.data_categories) == {
        "bank_account",
        "other_sensitive_data",
        "payment_card",
        "personal_id",
    }


def test_discovery_discards_stale_categories_when_model_verdict_is_clean() -> None:
    client = OllamaSensitiveContentDiscoveryClientImpl(
        base_url="http://localhost:11434",
        model_name="fake-discovery",
        request_timeout_seconds=1,
        context_tokens=1024,
        max_output_tokens=100,
        max_input_characters=1000,
    )

    result = client._parse(
        json.dumps({"has_sensitive": False, "categories": ["full name"]})
    )

    assert result.contains_sensitive_data is False
    assert result.risk_level.value == "low"
    assert result.data_categories == ()
