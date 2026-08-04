from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentSizeBytes:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("Document size must be a positive number")

