import json

from app.analysis.application.internal.services.content_sanitization_service import (
    ContentSanitizationService,
)
from app.analysis.application.internal.services.sensitive_data_detection_service import (
    SensitiveDataDetectionService,
)
from app.analysis.application.internal.services.sensitive_value_masking import (
    mask_sensitive_value,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)


def test_masking_formats_are_safe_and_recognizable() -> None:
    assert (
        mask_sensitive_value("4539459532651916", AnalysisFindingType.CREDIT_CARD)
        == "4539********1916"
    )
    assert (
        mask_sensitive_value("ana.gomez@example.com", AnalysisFindingType.EMAIL)
        == "a***@example.com"
    )
    password = mask_sensitive_value("S3nt1nel-Pr0d-2026!", AnalysisFindingType.PASSWORD)
    api_key = mask_sensitive_value(
        "sk-proj4Xm2QpLd8Rt6VbNc1Zk9WsYh3Ge7Uf5Ja",
        AnalysisFindingType.API_KEY,
    )
    assert password.startswith("S3n") and password.endswith("26!")
    assert api_key.startswith("sk-p") and api_key.endswith("f5Ja")
    assert "S3nt1nel" not in password
    assert "4Xm2QpLd" not in api_key


def test_sanitization_redacts_secrets_without_mutating_source() -> None:
    source = {
        "database": {"password": "S3nt1nel-Pr0d-2026!"},
        "contact": {"email": "ana.gomez@example.com", "phone": "+54 11 5555-0101"},
        "payment": {"card_number": "4539459532651916", "cvv": "836"},
    }
    findings = SensitiveDataDetectionService().scan(source)

    sanitized = ContentSanitizationService().sanitize(source, findings)

    assert source["database"]["password"] == "S3nt1nel-Pr0d-2026!"
    assert sanitized["database"]["password"] == "[REDACTED_PASSWORD]"
    assert sanitized["payment"]["card_number"] == "[REDACTED_CARD]"
    assert sanitized["payment"]["cvv"] == "[REDACTED_CVV]"
    assert sanitized["contact"]["email"] == "a***@example.com"
    rendered = json.dumps(sanitized)
    assert "S3nt1nel-Pr0d-2026!" not in rendered
    assert "4539459532651916" not in rendered
    assert "ana.gomez@example.com" not in rendered
