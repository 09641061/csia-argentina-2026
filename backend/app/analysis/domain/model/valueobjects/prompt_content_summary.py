from dataclasses import dataclass

from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects


@dataclass(frozen=True, slots=True)
class PromptContentSummary:
    """Masked, structural description of a free-text prompt."""

    character_count: int
    word_count: int
    line_count: int
    language_hint: str
    masked_excerpt: str
    finding_counts: tuple[tuple[str, int], ...]
    data_categories: tuple[str, ...]
    estimated_subjects: EstimatedSubjects
    injection_markers: tuple[str, ...]
    truncated: bool

    def __post_init__(self) -> None:
        if self.character_count <= 0:
            raise ValueError("Prompt character count must be a positive number")
        if min(self.word_count, self.line_count) < 0:
            raise ValueError("Prompt counts cannot be negative")

    def to_prompt_payload(self) -> dict[str, object]:
        return {
            "character_count": self.character_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "language_hint": self.language_hint,
            "masked_excerpt": self.masked_excerpt,
            "finding_counts": dict(self.finding_counts),
            "data_categories": list(self.data_categories),
            "injection_markers": list(self.injection_markers),
        }
