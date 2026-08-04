from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentName:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Document name is required")

        if len(self.value.strip()) > 255:
            raise ValueError("Document name cannot exceed 255 characters")

