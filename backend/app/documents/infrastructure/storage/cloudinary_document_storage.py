from __future__ import annotations

import asyncio
from io import BytesIO
from uuid import uuid4

from app.core.settings import get_settings
from app.documents.application.internal.outboundservices.document_storage import (
    DocumentStorage,
)
from app.documents.domain.model.valueobjects.document_storage_reference import (
    CLOUDINARY_BACKEND,
    DocumentStorageReference,
)
from app.documents.infrastructure.storage.exceptions import (
    DocumentStorageNotConfiguredError,
    DocumentStorageReadError,
    DocumentStorageUploadError,
)
from app.documents.infrastructure.storage.safe_url_content_reader import (
    SafeUrlContentReader,
)

CLOUDINARY_ALLOWED_HOSTS = frozenset({"res.cloudinary.com"})
CLOUDINARY_EXTENSION_BY_MIME_TYPE = {
    "application/json": ".json",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}


class CloudinaryDocumentStorage(DocumentStorage):
    """
    Remote storage used by the deployment (DOCUMENT_STORAGE_BACKEND=cloudinary).

    The uploaded bytes leave the machine before the security review runs, so use
    it only for content the organization accepts sending to a third party.
    DOCUMENT_STORAGE_BACKEND=local keeps everything on disk instead.
    """

    def __init__(self, folder: str = "sentinel-ai-guard/documents", max_content_bytes: int | None = None) -> None:
        settings = get_settings()
        missing_settings = [
            name
            for name, value in {
                "CLOUDINARY_CLOUD_NAME": settings.cloudinary_cloud_name,
                "CLOUDINARY_API_KEY": settings.cloudinary_api_key,
                "CLOUDINARY_API_SECRET": settings.cloudinary_api_secret,
            }.items()
            if not value.strip()
        ]
        if missing_settings:
            raise DocumentStorageNotConfiguredError(
                f"Cloudinary is not configured. Missing: {', '.join(missing_settings)}"
            )

        import cloudinary

        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        self._folder = folder.strip("/")
        self._max_content_bytes = max_content_bytes or settings.max_document_size_bytes
        self._reader = SafeUrlContentReader(
            allowed_hosts=CLOUDINARY_ALLOWED_HOSTS,
            max_content_bytes=self._max_content_bytes,
        )

    @property
    def backend_name(self) -> str:
        return CLOUDINARY_BACKEND

    async def store(self, content: bytes, content_type: str) -> DocumentStorageReference:
        if not content:
            raise DocumentStorageUploadError("Document content is required")
        if len(content) > self._max_content_bytes:
            raise DocumentStorageUploadError("Document exceeds the maximum allowed size")
        url = await asyncio.to_thread(self._store_sync, content, content_type)
        return DocumentStorageReference.for_cloudinary(url)

    async def read(self, reference: DocumentStorageReference) -> bytes:
        if reference.backend != CLOUDINARY_BACKEND:
            raise DocumentStorageReadError("This reference does not belong to Cloudinary storage")
        return await self._reader.read(reference.key)

    def _store_sync(self, content: bytes, content_type: str) -> str:
        import cloudinary.uploader

        extension = CLOUDINARY_EXTENSION_BY_MIME_TYPE.get(content_type)
        if extension is None:
            raise DocumentStorageUploadError(
                "Cloudinary cannot store this document content type"
            )

        upload_file = BytesIO(content)
        upload_file.name = f"{uuid4().hex}{extension}"

        try:
            result = cloudinary.uploader.upload(
                upload_file,
                resource_type="raw",
                folder=self._folder,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                context={"content_type": content_type},
            )
        except Exception as error:
            raise DocumentStorageUploadError("Cloudinary document upload failed") from error

        document_url = result.get("secure_url") or result.get("url")
        if not isinstance(document_url, str) or not document_url.startswith("https://"):
            raise DocumentStorageUploadError("Cloudinary upload did not return a secure URL")
        return document_url
