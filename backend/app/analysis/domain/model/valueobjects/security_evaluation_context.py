from dataclasses import dataclass

from app.analysis.domain.model.valueobjects.analyzed_content_type import (
    AnalyzedContentType,
)
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects


@dataclass(frozen=True, slots=True)
class SecurityEvaluationContext:
    """
    The only thing the security model ever receives.

    Everything inside is already masked and summarized, which is why a prompt
    and an extracted document can share one evaluation contract: the model reasons
    about shape, categories and scale, never about raw values.
    """

    content_type: AnalyzedContentType
    reference_label: str
    approximate_size: int
    estimated_subjects: EstimatedSubjects
    truncated: bool
    structure: dict[str, object]

    def __post_init__(self) -> None:
        if not self.reference_label.strip():
            raise ValueError("A masked reference label is required")
        if self.approximate_size <= 0:
            raise ValueError("Approximate size must be a positive number")

    def to_prompt_payload(self) -> dict[str, object]:
        return {
            "content_type": self.content_type.value,
            "reference": self.reference_label,
            "approximate_size": self.approximate_size,
            "estimated_subjects": self.estimated_subjects.value,
            "truncated": self.truncated,
            "structure": self.structure,
        }
