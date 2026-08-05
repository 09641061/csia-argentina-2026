from typing import Protocol


class DecisionContextValidationError(ValueError):
    """The submitted chat content is not valid for the secure-query capability."""


class DecisionContextFacade(Protocol):
    async def execute_authorized_query(
        self,
        *,
        prompt: str | None,
        document_filename: str | None,
        document_mime_type: str | None,
        document_content: bytes | None,
    ) -> dict[str, object | None]: ...
