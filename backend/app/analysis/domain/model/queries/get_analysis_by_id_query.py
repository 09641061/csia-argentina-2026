from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetAnalysisByIdQuery:
    analysis_id: int
    requested_by: str = "system"

    def __post_init__(self) -> None:
        if self.analysis_id <= 0:
            raise ValueError("Analysis ID must be a positive number")
        if not self.requested_by.strip():
            raise ValueError("Authenticated user is required")
