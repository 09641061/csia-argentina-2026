from typing import Protocol


class DocumentsContextError(RuntimeError):
    """A safe failure exposed at the Documents bounded-context boundary."""


class UnsupportedDocumentContextTypeError(DocumentsContextError):
    pass


class DocumentContextTooLargeError(DocumentsContextError):
    pass


class InvalidDocumentContextContentError(DocumentsContextError):
    pass


class DocumentsContextFacade(Protocol):
    async def register_document(
        self, *, filename: str, mime_type: str, content: bytes
    ) -> dict[str, object]: ...

    async def find_document(self, document_id: int) -> dict[str, object] | None: ...

    async def read_document_content(self, document_id: int) -> bytes: ...

    async def record_review_outcome(
        self, *, document_id: int, status: str, blocked_reason: str | None
    ) -> None: ...
