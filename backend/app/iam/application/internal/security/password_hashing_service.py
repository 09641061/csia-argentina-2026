from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError


class PasswordHashingService:
    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()
        self._dummy_hash = self._password_hash.hash(
            "claude-dummy-password-never-used-for-login-2026"
        )

    def hash(self, password: str) -> str:
        return self._password_hash.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._password_hash.verify(password, password_hash)
        except UnknownHashError:
            return False

    def verify_dummy(self, password: str) -> None:
        self._password_hash.verify(password, self._dummy_hash)
