from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath

from app.shared.domain.text_masking import mask_free_text

_MAX_LENGTH = 120
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True, slots=True)
class DocumentDisplayName:
    """
    Safe, human-readable label for an uploaded document.

    A filename is untrusted input: it may carry directory components, control
    characters or sensitive values such as an email or a token. Only this
    normalized, masked label is stored and shown; the original string is never
    persisted or used to build a path.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Document display name is required")
        if len(self.value) > _MAX_LENGTH:
            raise ValueError(f"Document display name cannot exceed {_MAX_LENGTH} characters")

    @classmethod
    def from_original_filename(cls, original_filename: str) -> "DocumentDisplayName":
        candidate = original_filename or ""
        candidate = PureWindowsPath(PurePosixPath(candidate).name).name
        candidate = _CONTROL_CHARACTERS.sub("", candidate).strip().strip(".")
        candidate = mask_free_text(candidate)
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if not candidate:
            candidate = "documento.json"
        return cls(candidate[:_MAX_LENGTH])
