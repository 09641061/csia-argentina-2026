from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MaskedFindingSummary:
    """A finding as the audit trail keeps it: typed, located and already masked."""

    origin: str
    finding_type: str
    severity: str
    title: str
    location: str
    masked_evidence: str
    occurrences: int = 1
    is_placeholder: bool = False

    def __post_init__(self) -> None:
        if self.origin not in {"prompt", "document"}:
            raise ValueError("Finding origin must be prompt or document")
        if not self.finding_type.strip():
            raise ValueError("Finding type is required")
        if not self.masked_evidence.strip():
            raise ValueError("Masked evidence is required")
        if self.occurrences <= 0:
            raise ValueError("Occurrences must be a positive number")
