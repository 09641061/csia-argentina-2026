from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentStoragePath:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Document storage path is required")
