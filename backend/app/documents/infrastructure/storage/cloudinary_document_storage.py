from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import PurePath

import cloudinary
import cloudinary.uploader

from app.core.settings import get_settings
from app.documents.application.internal.outboundservices.document_storage import DocumentStorage
from app.documents.infrastructure.storage.exceptions import DocumentStorageUploadError


class CloudinaryDocumentStorage(DocumentStorage):
    def __init__(self, folder: str = "sentinel-ai-guard/documents") -> None:
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
            raise DocumentStorageUploadError(
                f"Cloudinary is not configured. Missing: {', '.join(missing_settings)}"
            )

        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        self._folder = folder.strip("/")

    async def store(self, original_filename: str, content: bytes, content_type: str) -> str:
        return await asyncio.to_thread(
            self._store_sync,
            original_filename,
            content,
            content_type,
        )

    def _store_sync(self, original_filename: str, content: bytes, content_type: str) -> str:
        upload_file = BytesIO(content)
        upload_file.name = self._safe_filename(original_filename)

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
        if not isinstance(document_url, str) or not document_url.strip():
            raise DocumentStorageUploadError("Cloudinary upload did not return a document URL")

        return document_url

    def _safe_filename(self, original_filename: str) -> str:
        filename = PurePath(original_filename).name.strip()
        return filename or "document.json"
