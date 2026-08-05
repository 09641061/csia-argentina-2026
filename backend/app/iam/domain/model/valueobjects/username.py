from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Username:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("Username is required")
        if len(normalized) > 64:
            raise ValueError("Username cannot exceed 64 characters")
        object.__setattr__(self, "value", normalized)
