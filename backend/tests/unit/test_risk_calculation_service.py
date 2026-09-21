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


def test_model_cannot_escalate_above_its_own_two_tracks() -> None:
    """
    A verdict the model will not attribute to a track is not evidence.

    This is the shape that blocked a photograph of a public figure: "medium"
    overall, secrets "none", personal data "low", and a summary saying the
    content posed no risk.
    """

    result = RiskCalculationService().calculate(
        findings=[],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=OllamaAnalysisInterpretation(
            risk_level=AnalysisRiskLevel.MEDIUM,
            secrets_risk=SecretsRiskLevel.NONE,
            personal_data_risk=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=False,
            data_categories=(),
            estimated_subjects=EstimatedSubjects.ZERO,
            summary="The document is a photograph, posing no immediate risk.",
            rationale="The structure describes an image and no identifiers are present.",
        ),
    )

    assert result.risk_level == AnalysisRiskLevel.LOW


def test_model_escalation_counts_when_it_names_the_track() -> None:
    """The other half of the rule: an attributed escalation still raises."""

    result = RiskCalculationService().calculate(
        findings=[],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=OllamaAnalysisInterpretation(
            risk_level=AnalysisRiskLevel.HIGH,
            secrets_risk=SecretsRiskLevel.HIGH,
            personal_data_risk=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=False,
            data_categories=("api_key",),
            estimated_subjects=EstimatedSubjects.ZERO,
            summary="A credential is present in the reviewed content.",
            rationale="The sample exposes a value with the shape of an API credential.",
        ),
    )

    assert result.risk_level == AnalysisRiskLevel.HIGH
    assert result.secrets_risk == SecretsRiskLevel.HIGH


def test_unattributed_escalation_does_not_confirm_a_medium_confidence_discovery() -> None:
    result = RiskCalculationService().calculate(
        findings=[],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=OllamaAnalysisInterpretation(
            risk_level=AnalysisRiskLevel.MEDIUM,
            secrets_risk=SecretsRiskLevel.NONE,
            personal_data_risk=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=False,
            data_categories=(),
            estimated_subjects=EstimatedSubjects.ZERO,
            summary="The document is a photograph with no sensitive material.",
            rationale="No identifiers or credential material appear in the sample.",
        ),
        discovery=SensitiveContentDiscovery(
            contains_sensitive_data=True,
            risk_level=AnalysisRiskLevel.HIGH,
            confidence=AnalysisConfidence.MEDIUM,
            data_categories=("credentials",),
            model_name="local-discovery-model",
        ),
    )

    assert result.discovery_confirmed is False
    assert result.risk_level == AnalysisRiskLevel.LOW


def test_tampering_still_forces_a_high_floor_on_clean_tracks() -> None:
    """Escalation without a track is still allowed through the tampering lever."""

    result = RiskCalculationService().calculate(
        findings=[],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=OllamaAnalysisInterpretation(
            risk_level=AnalysisRiskLevel.HIGH,
            secrets_risk=SecretsRiskLevel.NONE,
            personal_data_risk=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=True,
            data_categories=(),
            estimated_subjects=EstimatedSubjects.ZERO,
            summary="The content tries to override the review instructions.",
            rationale="The sample instructs the reviewer to ignore its own rules.",
        ),
    )

    assert result.tampering_suspected is True
    assert result.risk_level == AnalysisRiskLevel.HIGH


def model_claiming_secrets(
    *,
    categories: tuple[str, ...],
    secrets: SecretsRiskLevel = SecretsRiskLevel.MEDIUM,
) -> OllamaAnalysisInterpretation:
    return OllamaAnalysisInterpretation(
        risk_level=AnalysisRiskLevel(_SECRETS_TO_RISK[secrets]),
        secrets_risk=secrets,
        personal_data_risk=AnalysisRiskLevel.LOW,
        confidence=AnalysisConfidence.HIGH,
        tampering_suspected=False,
        data_categories=categories,
        estimated_subjects=EstimatedSubjects.ZERO,
        summary="The reviewed content was classified by the local model.",
        rationale="The model reported a secrets track above none.",
    )


_SECRETS_TO_RISK = {
    SecretsRiskLevel.MEDIUM: "medium",
    SecretsRiskLevel.HIGH: "high",
    SecretsRiskLevel.CRITICAL: "critical",
}


def test_secrets_claim_without_a_credential_category_is_discarded() -> None:
    """
    "There is text here" is not a credential.

    The local model used the secrets track as a catch-all: a meme caption came
    back as secrets "medium" with category "text", a settings screenshot with
    "language", a photo of a footballer with "api_key" but no finding behind it.
    A credential claim has to name a credential.
    """

    for junk in (("text",), ("image",), ("language",), ("document_type",), ()):
        result = RiskCalculationService().calculate(
            findings=[],
            estimated_subjects=EstimatedSubjects.ZERO,
            interpretation=model_claiming_secrets(categories=junk),
        )
        assert result.secrets_risk == SecretsRiskLevel.NONE, junk
        assert result.risk_level == AnalysisRiskLevel.LOW, junk


def test_secrets_claim_that_names_a_credential_still_counts() -> None:
    """The model keeps catching what the deterministic patterns missed."""

    for category in ("api_key", "password", "private_key", "connection_string", "token"):
        result = RiskCalculationService().calculate(
            findings=[],
            estimated_subjects=EstimatedSubjects.ZERO,
            interpretation=model_claiming_secrets(
                categories=(category,), secrets=SecretsRiskLevel.HIGH
            ),
        )
        assert result.secrets_risk == SecretsRiskLevel.HIGH, category
        assert result.risk_level == AnalysisRiskLevel.HIGH, category


def test_secrets_claim_backed_by_a_deterministic_finding_still_counts() -> None:
    """A supplied secret finding is attribution enough, whatever the model names."""

    result = RiskCalculationService().calculate(
        findings=[finding(AnalysisFindingType.API_KEY, "$.config.api_key")],
        estimated_subjects=EstimatedSubjects.ZERO,
        interpretation=model_claiming_secrets(
            categories=("other",), secrets=SecretsRiskLevel.CRITICAL
        ),
    )

    assert result.secrets_risk == SecretsRiskLevel.CRITICAL


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
