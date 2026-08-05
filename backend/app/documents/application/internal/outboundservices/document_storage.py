from typing import Protocol

from app.documents.domain.model.valueobjects.document_storage_reference import (
    DocumentStorageReference,
)


class DocumentStorage(Protocol):
    """
    Controlled storage adapter for uploaded documents.

    The original filename is deliberately absent from this contract: the adapter
    generates its own opaque internal name so a crafted filename can never steer
    a write or a read outside the configured root.
    """

    @property
    def backend_name(self) -> str: ...

    async def store(self, content: bytes, content_type: str) -> DocumentStorageReference: ...

    async def read(self, reference: DocumentStorageReference) -> bytes: ...
