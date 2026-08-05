import re
from dataclasses import dataclass

from app.iam.domain.exceptions import WeakPasswordError
from app.iam.domain.model.valueobjects.username import Username


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    username: str
    password: str

    def __post_init__(self) -> None:
        Username(self.username)
        if len(self.password) < 8:
            raise WeakPasswordError("Password must contain at least 8 characters")
        if len(self.password) > 128:
            raise WeakPasswordError("Password cannot exceed 128 characters")
        if (
            re.search(r"[A-Za-z]", self.password) is None
            or re.search(r"\d", self.password) is None
        ):
            raise WeakPasswordError(
                "Password must contain at least one letter and one number"
            )
