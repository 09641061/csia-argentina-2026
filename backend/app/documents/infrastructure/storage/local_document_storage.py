from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from app.documents.application.internal.outboundservices.document_storage import (
    DocumentStorage,
)
from app.documents.domain.model.valueobjects.document_storage_reference import (
    LOCAL_BACKEND,
    DocumentStorageReference,
)
from app.documents.infrastructure.storage.exceptions import (
    DocumentStorageReadError,
    DocumentStorageUploadError,
)


class LocalDocumentStorage(DocumentStorage):
    """
    Default storage adapter: a private directory inside the deployment.

    Sentinel exists to stop confidential content from leaving the organization,
    so an uploaded document must not travel to a third party before the security
    review runs. Files are written with generated opaque names, and every read is
    confined to the configured root, which makes path traversal and arbitrary
    file reads impossible even with a hostile reference.
    """

    def __init__(self, root_directory: Path, max_content_bytes: int) -> None:
        if max_content_bytes <= 0:
            raise ValueError("Maximum content size must be positive")
        self._root = root_directory.resolve()
        self._max_content_bytes = max_content_bytes
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def backend_name(self) -> str:
        return LOCAL_BACKEND

    async def store(self, content: bytes, content_type: str) -> DocumentStorageReference:
        del content_type
        if not content:
            raise DocumentStorageUploadError("Document content is required")
        if len(content) > self._max_content_bytes:
            raise DocumentStorageUploadError("Document exceeds the maximum allowed size")
        reference = DocumentStorageReference.for_local(f"{uuid4().hex}.bin")
        await asyncio.to_thread(self._write, reference.key, content)
        return reference

    async def read(self, reference: DocumentStorageReference) -> bytes:
        if reference.backend != LOCAL_BACKEND:
            raise DocumentStorageReadError("This reference does not belong to local storage")
        return await asyncio.to_thread(self._read, reference.key)

    def _write(self, key: str, content: bytes) -> None:
        target = self._resolve_inside_root(key)
        try:
            target.write_bytes(content)
        except OSError as error:
            raise DocumentStorageUploadError("The document could not be stored") from error

    def _read(self, key: str) -> bytes:
        target = self._resolve_inside_root(key)
        try:
            content = target.read_bytes()
        except FileNotFoundError as error:
            raise DocumentStorageReadError("The stored document is no longer available") from error
        except OSError as error:
            raise DocumentStorageReadError("The stored document could not be read") from error
        if len(content) > self._max_content_bytes:
            raise DocumentStorageReadError("The stored document exceeds the analysis size limit")
        if not content:
            raise DocumentStorageReadError("The stored document is empty")
        return content

    def _resolve_inside_root(self, key: str) -> Path:
        if "/" in key or "\\" in key:
            raise DocumentStorageReadError("Rejected nested storage key")
        candidate = (self._root / key).resolve()
        if candidate.parent != self._root:
            raise DocumentStorageReadError("Rejected storage key outside the private root")
        return candidate
