from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidateAccessTokenQuery:
    access_token: str

    def __post_init__(self) -> None:
        if not self.access_token.strip():
            raise ValueError("Access token is required")
