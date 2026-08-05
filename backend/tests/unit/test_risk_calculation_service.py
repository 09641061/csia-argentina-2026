from app.analysis.application.internal.services.risk_calculation_service import (
    RiskCalculationService,
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
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel
from app.analysis.domain.model.valueobjects.sensitive_content_discovery import (
    SensitiveContentDiscovery,
)


def finding(
    finding_type: AnalysisFindingType, path: str, *, placeholder: bool = False
) -> AnalysisFinding:
    severity = AnalysisFindingSeverity.MEDIUM if placeholder else AnalysisFindingSeverity.HIGH
    if finding_type == AnalysisFindingType.PRIVATE_KEY:
        severity = AnalysisFindingSeverity.CRITICAL
    return AnalysisFinding(
        finding_id=f"f-{finding_type.value}",
        finding_type=finding_type,
        severity=severity,
        title="Synthetic finding",
        description="Safe test finding",
        json_path=path,
        evidence="[REDACTED]",
        detection_method="test_rule",
        confidence=AnalysisConfidence.HIGH,
        data_category=finding_type.value,
        is_placeholder=placeholder,
    )


def low_model(
    subjects: EstimatedSubjects = EstimatedSubjects.ZERO,
) -> OllamaAnalysisInterpretation:
    return OllamaAnalysisInterpretation(
        risk_level=AnalysisRiskLevel.LOW,
        secrets_risk=SecretsRiskLevel.NONE,
        personal_data_risk=AnalysisRiskLevel.LOW,
        confidence=AnalysisConfidence.HIGH,
        tampering_suspected=False,
        data_categories=(),
        estimated_subjects=subjects,
        summary="No contextual elevation required.",
        rationale="Only masked finding identifiers were evaluated.",
    )


def test_private_key_cannot_be_lowered_by_model() -> None:
    result = RiskCalculationService().calculate(
        findings=[finding(AnalysisFindingType.PRIVATE_KEY, "$.key")],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=low_model(),
    )
    assert result.risk_level == AnalysisRiskLevel.CRITICAL
    assert result.secrets_risk == SecretsRiskLevel.CRITICAL


def test_card_and_cvv_under_same_object_are_critical() -> None:
    findings = [
        finding(AnalysisFindingType.CREDIT_CARD, "$.payment.card_number"),
        finding(AnalysisFindingType.CVV, "$.payment.cvv"),
    ]
    result = RiskCalculationService().calculate(
        findings=findings,
        estimated_subjects=EstimatedSubjects.ONE_TO_FIVE,
        interpretation=low_model(EstimatedSubjects.ONE_TO_FIVE),
    )
    assert result.risk_level == AnalysisRiskLevel.CRITICAL
    assert result.personal_data_risk == AnalysisRiskLevel.CRITICAL


def test_api_key_is_at_least_high_and_placeholder_is_medium() -> None:
    real = RiskCalculationService().calculate(
        findings=[finding(AnalysisFindingType.API_KEY, "$.api_key")],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=low_model(),
    )
    placeholder = RiskCalculationService().calculate(
        findings=[finding(AnalysisFindingType.API_KEY, "$.api_key", placeholder=True)],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=low_model(),
    )
    assert real.risk_level == AnalysisRiskLevel.HIGH
    assert placeholder.risk_level == AnalysisRiskLevel.MEDIUM


def test_prompt_injection_sets_tampering_and_high_floor() -> None:
    result = RiskCalculationService().calculate(
        findings=[finding(AnalysisFindingType.PROMPT_INJECTION, "$.notes")],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=low_model(),
    )
    assert result.tampering_suspected is True
    assert result.risk_level == AnalysisRiskLevel.HIGH


def test_clean_content_stays_low() -> None:
    result = RiskCalculationService().calculate(
        findings=[],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=low_model(),
    )
    assert result.risk_level == AnalysisRiskLevel.LOW
    assert result.secrets_risk == SecretsRiskLevel.NONE


def test_medium_confidence_discovery_requires_independent_confirmation() -> None:
    result = RiskCalculationService().calculate(
        findings=[],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=low_model(),
        discovery=SensitiveContentDiscovery(
            contains_sensitive_data=True,
            risk_level=AnalysisRiskLevel.HIGH,
            confidence=AnalysisConfidence.MEDIUM,
            data_categories=("bank_account", "credentials"),
            model_name="local-discovery-model",
        ),
    )

    assert result.risk_level == AnalysisRiskLevel.LOW
    assert result.data_categories == ()
    assert result.discovery_confirmed is False


def test_high_confidence_discovery_can_block_without_deterministic_findings() -> None:
    result = RiskCalculationService().calculate(
        findings=[],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=low_model(),
        discovery=SensitiveContentDiscovery(
            contains_sensitive_data=True,
            risk_level=AnalysisRiskLevel.MEDIUM,
            confidence=AnalysisConfidence.HIGH,
            data_categories=("full_name", "personal_id"),
            model_name="local-discovery-model",
        ),
    )

    assert result.risk_level == AnalysisRiskLevel.MEDIUM
    assert set(result.data_categories) == {"full_name", "personal_id"}
    assert result.discovery_confirmed is True
