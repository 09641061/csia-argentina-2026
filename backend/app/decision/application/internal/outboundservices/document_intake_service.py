from dataclasses import dataclass
from typing import Protocol

from app.decision.domain.model.valueobjects.security_decision import SecurityDecision


@dataclass(frozen=True, slots=True)
class RegisteredDocument:
    document_id: int
    display_name: str

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")


class DocumentIntakeService(Protocol):
    """Anti-corruption contract towards Documents."""

    async def register_document(
        self,
        *,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> RegisteredDocument: ...

    async def read_allowed_document_content(
        self,
        document_id: int,
    ) -> dict[str, object] | list[object]: ...

    async def record_review_outcome(
        self,
        *,
        document_id: int,
        decision: SecurityDecision,
        reason: str,
    ) -> None: ...
