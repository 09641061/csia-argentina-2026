import re
from dataclasses import dataclass

_USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]+$")


@dataclass(frozen=True, slots=True)
class Username:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().casefold()
        if len(normalized) < 3:
            raise ValueError("Username must contain at least 3 characters")
        if len(normalized) > 64:
            raise ValueError("Username cannot exceed 64 characters")
        if _USERNAME_PATTERN.fullmatch(normalized) is None:
            raise ValueError(
                "Username may contain only letters, numbers, dots, hyphens and underscores"
            )
        object.__setattr__(self, "value", normalized)
