from __future__ import annotations

from dataclasses import dataclass

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

_RISK_ORDER = {
    AnalysisRiskLevel.LOW: 0,
    AnalysisRiskLevel.MEDIUM: 1,
    AnalysisRiskLevel.HIGH: 2,
    AnalysisRiskLevel.CRITICAL: 3,
}
_SECRET_ORDER = {
    SecretsRiskLevel.NONE: 0,
    SecretsRiskLevel.MEDIUM: 1,
    SecretsRiskLevel.HIGH: 2,
    SecretsRiskLevel.CRITICAL: 3,
}
_SECRETS_AS_RISK = {
    SecretsRiskLevel.NONE: AnalysisRiskLevel.LOW,
    SecretsRiskLevel.MEDIUM: AnalysisRiskLevel.MEDIUM,
    SecretsRiskLevel.HIGH: AnalysisRiskLevel.HIGH,
    SecretsRiskLevel.CRITICAL: AnalysisRiskLevel.CRITICAL,
}
_CONFIDENCE_ORDER = {
    AnalysisConfidence.LOW: 0,
    AnalysisConfidence.MEDIUM: 1,
    AnalysisConfidence.HIGH: 2,
}
_SUBJECT_ORDER = {
    EstimatedSubjects.ZERO: 0,
    EstimatedSubjects.ONE_TO_FIVE: 1,
    EstimatedSubjects.SIX_TO_ONE_HUNDRED: 2,
    EstimatedSubjects.OVER_ONE_HUNDRED: 3,
    EstimatedSubjects.UNKNOWN: -1,
}
_SECRET_TYPES = {
    AnalysisFindingType.PASSWORD,
    AnalysisFindingType.API_KEY,
    AnalysisFindingType.TOKEN,
    AnalysisFindingType.ACCESS_TOKEN,
    AnalysisFindingType.REFRESH_TOKEN,
    AnalysisFindingType.SESSION_ID,
    AnalysisFindingType.SESSION_COOKIE,
    AnalysisFindingType.AWS_ACCESS_KEY,
    AnalysisFindingType.CONNECTION_STRING,
    AnalysisFindingType.PRIVATE_KEY,
    AnalysisFindingType.SECRET,
}
_DIRECT_PERSONAL_TYPES = {
    AnalysisFindingType.EMAIL,
    AnalysisFindingType.FULL_NAME,
    AnalysisFindingType.PHONE,
    AnalysisFindingType.PERSONAL_ID,
    AnalysisFindingType.PASSPORT,
}
_FINANCIAL_TYPES = {
    AnalysisFindingType.CREDIT_CARD,
    AnalysisFindingType.CVV,
    AnalysisFindingType.CARD_EXPIRATION,
    AnalysisFindingType.BANK_ACCOUNT,
    AnalysisFindingType.FINANCIAL_DATA,
}
_DISCOVERY_SECRET_CATEGORIES = {
    "api_key",
    "connection_string",
    "credentials",
    "password",
    "private_key",
    "session_id",
    "token",
}
# The vocabulary a credential claim has to speak. Anything outside it — "text",
# "image", "language", "document_type" — is the model describing the payload, not
# reporting a secret.
_CREDENTIAL_CATEGORIES = (
    _DISCOVERY_SECRET_CATEGORIES
    | {finding_type.value for finding_type in _SECRET_TYPES}
    | {"credential", "secrets", "aws_secret_key", "client_secret"}
)
_DISCOVERY_PERSONAL_CATEGORIES = {
    "address",
    "bank_account",
    "biometric_data",
    "contact_data",
    "cvv",
    "email",
    "financial_data",
    "full_name",
    "health_data",
    "ip_address",
    "location",
    "passport",
    "payment_card",
    "personal_id",
    "phone",
}


@dataclass(frozen=True, slots=True)
class FinalRiskAssessment:
    risk_level: AnalysisRiskLevel
    secrets_risk: SecretsRiskLevel
    personal_data_risk: AnalysisRiskLevel
    confidence: AnalysisConfidence
    tampering_suspected: bool
    data_categories: tuple[str, ...]
    estimated_subjects: EstimatedSubjects
    discovery_confirmed: bool


class RiskCalculationService:
    def calculate(
        self,
        *,
        findings: list[AnalysisFinding],
        estimated_subjects: EstimatedSubjects,
        interpretation: OllamaAnalysisInterpretation,
        discovery: SensitiveContentDiscovery | None = None,
    ) -> FinalRiskAssessment:
        """
        Combine the deterministic evidence with the model interpretation.

        Every combination is a maximum, never an average: the model can raise a
        risk but it can never lower what the deterministic rules already
        confirmed.

        What the model cannot do is raise the risk without saying what for. Its
        verdict travels in two tracks, secrets and personal data, and its overall
        `risk_level` is defined as the higher of them; both are folded in below.
        A `risk_level` above both of its own tracks is an opinion with no stated
        evidence, and it used to be enough to block: a photograph of a public
        figure came back "medium" with secrets "none", personal data "low" and a
        summary reading "posing no immediate risk". Escalation now has to be
        attributed — to a track, to a deterministic finding, to the discovery
        pass, or to `tampering_suspected`, which still forces a "high" floor.
        """

        deterministic_secrets = self._deterministic_secrets_risk(findings)
        deterministic_personal = self._deterministic_personal_risk(findings, estimated_subjects)
        model_secrets = self._attributable_model_secrets(interpretation, findings)
        secrets_risk = max(deterministic_secrets, model_secrets, key=_SECRET_ORDER.get)
        personal_risk = max(
            deterministic_personal,
            interpretation.personal_data_risk,
            key=_RISK_ORDER.get,
        )
        model_risk = self._attributable_model_risk(interpretation, model_secrets)
        discovery_confirmed = self._discovery_is_confirmed(
            discovery=discovery,
            findings=findings,
            model_risk=model_risk,
        )
        effective_discovery = discovery if discovery_confirmed else None
        if effective_discovery is not None:
            discovered_categories = set(effective_discovery.data_categories)
            if discovered_categories & _DISCOVERY_SECRET_CATEGORIES:
                discovered_secret_risk = SecretsRiskLevel(
                    effective_discovery.risk_level.value
                )
                secrets_risk = max(
                    secrets_risk,
                    discovered_secret_risk,
                    key=_SECRET_ORDER.get,
                )
            if discovered_categories & _DISCOVERY_PERSONAL_CATEGORIES:
                personal_risk = max(
                    personal_risk,
                    effective_discovery.risk_level,
                    key=_RISK_ORDER.get,
                )
        secrets_as_risk = _SECRETS_AS_RISK[secrets_risk]
        risk_level = max(
            secrets_as_risk,
            personal_risk,
            model_risk,
            (
                effective_discovery.risk_level
                if effective_discovery is not None
                else AnalysisRiskLevel.LOW
            ),
            key=_RISK_ORDER.get,
        )
        tampering = (
            interpretation.tampering_suspected
            or any(
                finding.finding_type == AnalysisFindingType.PROMPT_INJECTION
                for finding in findings
            )
            or (
                effective_discovery is not None
                and "prompt_injection" in effective_discovery.data_categories
            )
        )
        if tampering:
            risk_level = max(risk_level, AnalysisRiskLevel.HIGH, key=_RISK_ORDER.get)
        confidence = min(
            interpretation.confidence,
            self._deterministic_confidence(findings),
            (
                effective_discovery.confidence
                if effective_discovery is not None
                else AnalysisConfidence.HIGH
            ),
            key=_CONFIDENCE_ORDER.get,
        )
        categories = tuple(
            sorted(
                {
                    *interpretation.data_categories,
                    *(
                        effective_discovery.data_categories
                        if effective_discovery is not None
                        else ()
                    ),
                    *(
                        finding.data_category
                        for finding in findings
                        if finding.data_category
                    ),
                }
            )
        )
        final_subjects = max(
            estimated_subjects,
            interpretation.estimated_subjects,
            key=_SUBJECT_ORDER.get,
        )
        return FinalRiskAssessment(
            risk_level=risk_level,
            secrets_risk=secrets_risk,
            personal_data_risk=personal_risk,
            confidence=confidence,
            tampering_suspected=tampering,
            data_categories=categories,
            estimated_subjects=final_subjects,
            discovery_confirmed=discovery_confirmed,
        )

    def _attributable_model_secrets(
        self,
        interpretation: OllamaAnalysisInterpretation,
        findings: list[AnalysisFinding],
    ) -> SecretsRiskLevel:
        """
        The model's secrets verdict, kept only when it names a credential.

        This track means "an attacker could authenticate with something in here",
        so a claim on it has to say which credential. The small local model
        instead used it as a catch-all: a meme caption came back with secrets
        "medium" and category "text", a settings screenshot with "language", a
        photo of a footballer with "api_key" — none of them backed by a
        deterministic finding. A claim that names a real credential category, or
        that any finding supports, still passes through untouched, so the model
        keeps its job of catching what the patterns missed.
        """

        if interpretation.secrets_risk == SecretsRiskLevel.NONE:
            return SecretsRiskLevel.NONE
        if any(finding.finding_type in _SECRET_TYPES for finding in findings):
            return interpretation.secrets_risk
        if set(interpretation.data_categories) & _CREDENTIAL_CATEGORIES:
            return interpretation.secrets_risk
        return SecretsRiskLevel.NONE

    def _attributable_model_risk(
        self,
        interpretation: OllamaAnalysisInterpretation,
        model_secrets: SecretsRiskLevel,
    ) -> AnalysisRiskLevel:
        """
        The model's verdict, capped at what its own two tracks support.

        Its contract defines `risk_level` as the higher of `secrets_risk` and
        `personal_data_risk`, so anything above both is an escalation the model
        declined to justify.
        """

        return min(
            interpretation.risk_level,
            max(
                _SECRETS_AS_RISK[model_secrets],
                interpretation.personal_data_risk,
                key=_RISK_ORDER.get,
            ),
            key=_RISK_ORDER.get,
        )

    def _discovery_is_confirmed(
        self,
        *,
        discovery: SensitiveContentDiscovery | None,
        findings: list[AnalysisFinding],
        model_risk: AnalysisRiskLevel,
    ) -> bool:
        if discovery is None or not discovery.contains_sensitive_data:
            return False
        if discovery.confidence == AnalysisConfidence.HIGH:
            return True
        if any(not finding.is_placeholder for finding in findings):
            return True
        # An unattributed escalation is not independent confirmation either.
        return model_risk != AnalysisRiskLevel.LOW

    def _deterministic_secrets_risk(
        self, findings: list[AnalysisFinding]
    ) -> SecretsRiskLevel:
        risk = SecretsRiskLevel.NONE
        for finding in findings:
            if finding.finding_type not in _SECRET_TYPES:
                continue
            if (
                finding.finding_type == AnalysisFindingType.PRIVATE_KEY
                and not finding.is_placeholder
            ):
                return SecretsRiskLevel.CRITICAL
            candidate = (
                SecretsRiskLevel.MEDIUM
                if finding.is_placeholder
                else SecretsRiskLevel.HIGH
            )
            if finding.severity == AnalysisFindingSeverity.CRITICAL:
                candidate = SecretsRiskLevel.CRITICAL
            risk = max(risk, candidate, key=_SECRET_ORDER.get)
        return risk

    def _deterministic_personal_risk(
        self,
        findings: list[AnalysisFinding],
        estimated_subjects: EstimatedSubjects,
    ) -> AnalysisRiskLevel:
        types = {finding.finding_type for finding in findings}
        card_parents = {
            self._parent_path(finding.json_path)
            for finding in findings
            if finding.finding_type == AnalysisFindingType.CREDIT_CARD
        }
        cvv_parents = {
            self._parent_path(finding.json_path)
            for finding in findings
            if finding.finding_type == AnalysisFindingType.CVV
        }
        if card_parents & cvv_parents:
            return AnalysisRiskLevel.CRITICAL
        if not types & (
            _DIRECT_PERSONAL_TYPES | _FINANCIAL_TYPES | {AnalysisFindingType.IP_ADDRESS}
        ):
            return AnalysisRiskLevel.LOW
        if types & _FINANCIAL_TYPES:
            if estimated_subjects in {
                EstimatedSubjects.SIX_TO_ONE_HUNDRED,
                EstimatedSubjects.OVER_ONE_HUNDRED,
            }:
                return AnalysisRiskLevel.CRITICAL
            return AnalysisRiskLevel.HIGH
        if types & _DIRECT_PERSONAL_TYPES:
            if estimated_subjects == EstimatedSubjects.OVER_ONE_HUNDRED:
                return AnalysisRiskLevel.CRITICAL
            if estimated_subjects == EstimatedSubjects.SIX_TO_ONE_HUNDRED:
                return AnalysisRiskLevel.HIGH
            return AnalysisRiskLevel.MEDIUM
        return AnalysisRiskLevel.LOW

    def _deterministic_confidence(
        self, findings: list[AnalysisFinding]
    ) -> AnalysisConfidence:
        if not findings:
            return AnalysisConfidence.HIGH
        return min(
            (finding.confidence for finding in findings), key=_CONFIDENCE_ORDER.get
        )

    def _parent_path(self, path: str) -> str:
        dot_index = path.rfind(".")
        bracket_index = path.rfind("[")
        split_index = max(dot_index, bracket_index)
        return path[:split_index] if split_index > 0 else "$"
