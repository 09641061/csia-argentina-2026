from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

LOCAL_BACKEND = "local"
CLOUDINARY_BACKEND = "cloudinary"

_LOCAL_KEY_PATTERN = re.compile(r"^[0-9a-f]{32}\.(?:bin|json)$")
_HTTPS_URL_PATTERN = re.compile(r"^https://[^\s]+$")


@dataclass(frozen=True, slots=True)
class DocumentStorageReference:
    """
    Opaque, internal handle to a stored document.

    It is never a filesystem path chosen by a user and never leaves the backend:
    the public API exposes document identifiers instead. The local key is an
    opaque random name, so an attacker cannot steer a read towards an arbitrary
    file on the machine.
    """

    value: str

    SEPARATOR: ClassVar[str] = ":"

    def __post_init__(self) -> None:
        raw = self.value.strip()
        if not raw:
            raise ValueError("Document storage reference is required")
        if self.SEPARATOR not in raw:
            raise ValueError("Document storage reference must declare its backend")

        backend, _, key = raw.partition(self.SEPARATOR)
        backend = backend.strip().lower()
        key = key.strip()

        if backend == LOCAL_BACKEND:
            if not _LOCAL_KEY_PATTERN.fullmatch(key):
                raise ValueError("Local storage key must be an opaque generated name")
        elif backend == CLOUDINARY_BACKEND:
            if not _HTTPS_URL_PATTERN.fullmatch(key):
                raise ValueError("Cloudinary storage key must be an HTTPS URL")
        else:
            raise ValueError(f"Unsupported storage backend: {backend}")

        object.__setattr__(self, "value", f"{backend}{self.SEPARATOR}{key}")

    @classmethod
    def for_local(cls, key: str) -> DocumentStorageReference:
        return cls(f"{LOCAL_BACKEND}{cls.SEPARATOR}{key}")

    @classmethod
    def for_cloudinary(cls, url: str) -> DocumentStorageReference:
        return cls(f"{CLOUDINARY_BACKEND}{cls.SEPARATOR}{url}")

    @property
    def backend(self) -> str:
        return self.value.partition(self.SEPARATOR)[0]

    @property
    def key(self) -> str:
        return self.value.partition(self.SEPARATOR)[2]
