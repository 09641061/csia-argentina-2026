from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticateUserCommand:
    username: str
    password: str

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValueError("Username is required")
        if not self.password:
            raise ValueError("Password is required")
