from __future__ import annotations

from functools import lru_cache

from app.core.settings import get_settings
from app.documents.application.internal.outboundservices.document_storage import DocumentStorage
from app.documents.infrastructure.storage.local_document_storage import LocalDocumentStorage


@lru_cache(maxsize=1)
def get_document_storage() -> DocumentStorage:
    """
    Resolve the configured storage adapter.

    Local private storage is the default so the MVP runs with no external
    account; Cloudinary is only imported when it is explicitly enabled.
    """

    settings = get_settings()
    if settings.document_storage_backend == "cloudinary":
        from app.documents.infrastructure.storage.cloudinary_document_storage import (
            CloudinaryDocumentStorage,
        )

        return CloudinaryDocumentStorage(max_content_bytes=settings.max_document_size_bytes)

    return LocalDocumentStorage(
        root_directory=settings.document_storage_root,
        max_content_bytes=settings.max_document_size_bytes,
    )
