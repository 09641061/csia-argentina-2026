from __future__ import annotations

from dataclasses import dataclass

from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel

ALLOWED_DISCOVERY_CATEGORIES = frozenset(
    {
        "address",
        "api_key",
        "bank_account",
        "biometric_data",
        "confidential_business_data",
        "contact_data",
        "connection_string",
        "credentials",
        "cvv",
        "email",
        "financial_data",
        "full_name",
        "health_data",
        "ip_address",
        "location",
        "other_sensitive_data",
        "passport",
        "password",
        "payment_card",
        "personal_id",
        "phone",
        "private_key",
        "prompt_injection",
        "session_id",
        "token",
    }
)


@dataclass(frozen=True, slots=True)
class SensitiveContentDiscovery:
    """Value-free classification produced by the mandatory raw-content AI pass."""

    contains_sensitive_data: bool
    risk_level: AnalysisRiskLevel
    confidence: AnalysisConfidence
    data_categories: tuple[str, ...]
    model_name: str

    def __post_init__(self) -> None:
        if type(self.contains_sensitive_data) is not bool:
            raise ValueError("contains_sensitive_data must be a boolean")
        if not self.model_name.strip():
            raise ValueError("The discovery model name is required")
        if len(set(self.data_categories)) != len(self.data_categories):
            raise ValueError("Discovery categories cannot contain duplicates")
        if any(category not in ALLOWED_DISCOVERY_CATEGORIES for category in self.data_categories):
            raise ValueError("Discovery returned an unsupported data category")
        if self.contains_sensitive_data:
            if self.risk_level == AnalysisRiskLevel.LOW or not self.data_categories:
                raise ValueError(
                    "Sensitive discovery requires a non-low risk and at least one category"
                )
        elif self.risk_level != AnalysisRiskLevel.LOW or self.data_categories:
            raise ValueError(
                "A clean discovery must have low risk and no sensitive categories"
            )
