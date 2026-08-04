import asyncio
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import certifi

from app.analysis.application.internal.outboundservices.document_content_downloader import (
    DocumentContentDownloader,
)
from app.analysis.domain.exceptions import DocumentContentDownloadError


class UrlDocumentContentDownloader(DocumentContentDownloader):
    def __init__(self, max_content_bytes: int = 20 * 1024 * 1024) -> None:
        if max_content_bytes <= 0:
            raise ValueError("Maximum content size must be positive")
        self._max_content_bytes = max_content_bytes

    async def download(self, document_url: str) -> bytes:
        return await asyncio.to_thread(self._download, document_url)

    def _download(self, document_url: str) -> bytes:
        parsed_url = urlparse(document_url)
        if parsed_url.scheme not in {"http", "https"}:
            raise DocumentContentDownloadError(
                "Document storage reference must use HTTP or HTTPS"
            )
        context = ssl.create_default_context(cafile=certifi.where())
        try:
            with urlopen(document_url, context=context, timeout=30) as response:
                content = response.read(self._max_content_bytes + 1)
        except (HTTPError, URLError, TimeoutError) as error:
            raise DocumentContentDownloadError(
                "Unable to download the stored document"
            ) from error
        if len(content) > self._max_content_bytes:
            raise DocumentContentDownloadError(
                "Stored document exceeds the analysis size limit"
            )
        if not content:
            raise DocumentContentDownloadError("Stored document is empty")
        return content
