from dataclasses import dataclass

from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects


@dataclass(frozen=True, slots=True)
class DocumentStructureSummary:
    root_type: str
    approximate_size_bytes: int
    object_count: int
    array_count: int
    scalar_count: int
    record_count: int
    top_keys: tuple[str, ...]
    finding_counts: tuple[tuple[str, int], ...]
    data_categories: tuple[str, ...]
    estimated_subjects: EstimatedSubjects
    safe_sample: tuple[str, ...]
    truncated: bool
    prompt_injection_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.root_type not in {"object", "array"}:
            raise ValueError("JSON root type must be object or array")
        if self.approximate_size_bytes <= 0:
            raise ValueError("Document size must be a positive number")
        if (
            min(
                self.object_count,
                self.array_count,
                self.scalar_count,
                self.record_count,
            )
            < 0
        ):
            raise ValueError("Document structure counts cannot be negative")

    def to_prompt_payload(self) -> dict[str, object]:
        return {
            "root_type": self.root_type,
            "approximate_size_bytes": self.approximate_size_bytes,
            "object_count": self.object_count,
            "array_count": self.array_count,
            "scalar_count": self.scalar_count,
            "record_count": self.record_count,
            "top_keys": list(self.top_keys),
            "finding_counts": dict(self.finding_counts),
            "data_categories": list(self.data_categories),
            "estimated_subjects": self.estimated_subjects.value,
            "safe_sample": list(self.safe_sample),
            "truncated": self.truncated,
            "prompt_injection_paths": list(self.prompt_injection_paths),
        }
