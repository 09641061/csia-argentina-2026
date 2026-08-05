from dataclasses import dataclass, field

from app.decision.domain.model.valueobjects.masked_finding_summary import MaskedFindingSummary


@dataclass(frozen=True, slots=True)
class ReviewedContentAssessment:
    """
    What Decision & Audit is allowed to know about one security review.

    It is the anti-corruption shape of an Analysis execution: booleans and
    masked findings, never the reviewed content and never an Analysis entity or
    SQLAlchemy model.
    """

    analysis_id: int
    origin: str
    reference: str
    completed: bool
    risk_level: str | None
    tampering_suspected: bool
    has_confirmed_sensitive_findings: bool
    has_prompt_injection: bool
    data_categories: tuple[str, ...] = ()
    findings: tuple[MaskedFindingSummary, ...] = field(default_factory=tuple)
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.analysis_id <= 0:
            raise ValueError("Analysis ID must be a positive number")
        if self.origin not in {"prompt", "document"}:
            raise ValueError("Assessment origin must be prompt or document")

    @property
    def is_safe(self) -> bool:
        return (
            self.completed
            and self.risk_level == "low"
            and not self.tampering_suspected
            and not self.has_confirmed_sensitive_findings
            and not self.has_prompt_injection
        )
