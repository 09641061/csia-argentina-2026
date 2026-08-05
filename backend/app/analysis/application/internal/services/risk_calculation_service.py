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
        """

        deterministic_secrets = self._deterministic_secrets_risk(findings)
        deterministic_personal = self._deterministic_personal_risk(findings, estimated_subjects)
        secrets_risk = max(
            deterministic_secrets, interpretation.secrets_risk, key=_SECRET_ORDER.get
        )
        personal_risk = max(
            deterministic_personal,
            interpretation.personal_data_risk,
            key=_RISK_ORDER.get,
        )
        discovery_confirmed = self._discovery_is_confirmed(
            discovery=discovery,
            findings=findings,
            interpretation=interpretation,
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
        secrets_as_risk = (
            AnalysisRiskLevel(secrets_risk.value)
            if secrets_risk != SecretsRiskLevel.NONE
            else AnalysisRiskLevel.LOW
        )
        risk_level = max(
            secrets_as_risk,
            personal_risk,
            interpretation.risk_level,
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

    def _discovery_is_confirmed(
        self,
        *,
        discovery: SensitiveContentDiscovery | None,
        findings: list[AnalysisFinding],
        interpretation: OllamaAnalysisInterpretation,
    ) -> bool:
        if discovery is None or not discovery.contains_sensitive_data:
            return False
        if discovery.confidence == AnalysisConfidence.HIGH:
            return True
        if any(not finding.is_placeholder for finding in findings):
            return True
        return interpretation.risk_level != AnalysisRiskLevel.LOW

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
