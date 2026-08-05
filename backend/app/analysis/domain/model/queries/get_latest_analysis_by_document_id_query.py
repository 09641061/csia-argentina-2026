from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetLatestAnalysisByDocumentIdQuery:
    document_id: int

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")
