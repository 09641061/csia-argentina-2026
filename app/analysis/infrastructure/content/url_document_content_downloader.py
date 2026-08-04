import ssl
from urllib.request import urlopen
import asyncio

import certifi

from app.analysis.application.internal.outboundservices.document_content_downloader import DocumentContentDownloader


class UrlDocumentContentDownloader(DocumentContentDownloader):
    async def download(self, document_url: str) -> bytes:
        return await asyncio.to_thread(self._download, document_url)

    def _download(self, document_url: str) -> bytes:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(document_url, context=context, timeout=30) as response:
            return response.read()
