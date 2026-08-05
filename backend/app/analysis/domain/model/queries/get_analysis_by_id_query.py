from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetAnalysisByIdQuery:
    analysis_id: int

    def __post_init__(self) -> None:
        if self.analysis_id <= 0:
            raise ValueError("Analysis ID must be a positive number")
