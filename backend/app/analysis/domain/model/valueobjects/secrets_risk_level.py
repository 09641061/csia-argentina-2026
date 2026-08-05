from enum import StrEnum


class SecretsRiskLevel(StrEnum):
    NONE = "none"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
