from __future__ import annotations

import re
from dataclasses import dataclass

from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel

_REQUIRED_FIELDS = {
    "risk_level",
    "secrets_risk",
    "personal_data_risk",
    "confidence",
    "tampering_suspected",
    "data_categories",
    "estimated_subjects",
    "summary",
    "rationale",
}
_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_AWS_KEY_PATTERN = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
_SECRET_PATTERN = re.compile(
    r"(?i)\b(?:sk-(?:live|proj)|gh[opusr]_|xox[baprs]-|SG\.|hvs\.)[A-Za-z0-9_./+=-]{8,}"
)
_CONNECTION_STRING_PATTERN = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:]+:[^\s/@]+@")
_LABELED_SECRET_PATTERN = re.compile(
    r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token|secret)\b\s*[:=]\s*\S+"
)
_LONG_NUMBER_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){7,19}(?!\d)")


@dataclass(frozen=True, slots=True)
class OllamaAnalysisInterpretation:
    risk_level: AnalysisRiskLevel
    secrets_risk: SecretsRiskLevel
    personal_data_risk: AnalysisRiskLevel
    confidence: AnalysisConfidence
    tampering_suspected: bool
    data_categories: tuple[str, ...]
    estimated_subjects: EstimatedSubjects
    summary: str
    rationale: str

    def __post_init__(self) -> None:
        summary = self.summary.strip()
        rationale = self.rationale.strip()
        if not summary or not rationale:
            raise ValueError("Ollama summary and rationale are required")
        if len(summary) > 140:
            raise ValueError("Ollama summary cannot exceed 140 characters")
        if len(rationale) > 300:
            raise ValueError("Ollama rationale cannot exceed 300 characters")
        if type(self.tampering_suspected) is not bool:
            raise ValueError("Ollama tampering_suspected must be a boolean")
        if not all(
            category and re.fullmatch(r"[a-z0-9_\-]{1,50}", category)
            for category in self.data_categories
        ):
            raise ValueError("Ollama data_categories contains an invalid value")
        if len(set(self.data_categories)) != len(self.data_categories):
            raise ValueError("Ollama data_categories cannot contain duplicates")
        self._validate_risk_consistency()
        self._validate_safe_text(summary)
        self._validate_safe_text(rationale)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "rationale", rationale)

    @classmethod
    def from_payload(cls, payload: object) -> OllamaAnalysisInterpretation:
        if not isinstance(payload, dict):
            raise TypeError("Ollama response must be a JSON object")
        fields = set(payload)
        if fields != _REQUIRED_FIELDS:
            missing = sorted(_REQUIRED_FIELDS - fields)
            unexpected = sorted(fields - _REQUIRED_FIELDS)
            details: list[str] = []
            if missing:
                details.append(f"missing fields: {', '.join(missing)}")
            if unexpected:
                details.append(f"unexpected fields: {', '.join(unexpected)}")
            raise ValueError(f"Invalid Ollama response contract ({'; '.join(details)})")

        string_fields = (
            "risk_level",
            "secrets_risk",
            "personal_data_risk",
            "confidence",
            "estimated_subjects",
            "summary",
            "rationale",
        )
        if any(not isinstance(payload[field], str) for field in string_fields):
            raise ValueError("Ollama response string fields must contain strings")
        if type(payload["tampering_suspected"]) is not bool:
            raise ValueError("Ollama tampering_suspected must be a boolean")
        categories = payload["data_categories"]
        if not isinstance(categories, list) or not all(
            isinstance(item, str) for item in categories
        ):
            raise ValueError("Ollama data_categories must be an array of strings")

        try:
            return cls(
                risk_level=AnalysisRiskLevel(payload["risk_level"]),
                secrets_risk=SecretsRiskLevel(payload["secrets_risk"]),
                personal_data_risk=AnalysisRiskLevel(payload["personal_data_risk"]),
                confidence=AnalysisConfidence(payload["confidence"]),
                tampering_suspected=payload["tampering_suspected"],
                data_categories=tuple(categories),
                estimated_subjects=EstimatedSubjects(payload["estimated_subjects"]),
                summary=payload["summary"],
                rationale=payload["rationale"],
            )
        except ValueError as error:
            raise ValueError(f"Invalid Ollama response value: {error}") from error

    def _validate_risk_consistency(self) -> None:
        order = {
            AnalysisRiskLevel.LOW: 0,
            AnalysisRiskLevel.MEDIUM: 1,
            AnalysisRiskLevel.HIGH: 2,
            AnalysisRiskLevel.CRITICAL: 3,
        }
        secrets_as_risk = {
            SecretsRiskLevel.NONE: AnalysisRiskLevel.LOW,
            SecretsRiskLevel.MEDIUM: AnalysisRiskLevel.MEDIUM,
            SecretsRiskLevel.HIGH: AnalysisRiskLevel.HIGH,
            SecretsRiskLevel.CRITICAL: AnalysisRiskLevel.CRITICAL,
        }[self.secrets_risk]
        if order[self.risk_level] < max(
            order[secrets_as_risk], order[self.personal_data_risk]
        ):
            raise ValueError("Ollama risk_level cannot be lower than either risk track")

    def _validate_safe_text(self, value: str) -> None:
        if "-----BEGIN" in value.upper():
            raise ValueError("Ollama response contains private key material")
        if _EMAIL_PATTERN.search(value):
            raise ValueError("Ollama response contains a complete email address")
        if _AWS_KEY_PATTERN.search(value) or _SECRET_PATTERN.search(value):
            raise ValueError("Ollama response contains credential material")
        if _CONNECTION_STRING_PATTERN.search(value):
            raise ValueError(
                "Ollama response contains a credentialed connection string"
            )
        if _LABELED_SECRET_PATTERN.search(value):
            raise ValueError("Ollama response contains labeled credential material")
        for match in _LONG_NUMBER_PATTERN.finditer(value):
            digits = re.sub(r"\D", "", match.group(0))
            if len(digits) >= 7:
                raise ValueError(
                    "Ollama response contains a complete numeric identifier"
                )
