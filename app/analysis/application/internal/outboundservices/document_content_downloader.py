from typing import Protocol


class DocumentContentDownloader(Protocol):
    async def download(self, document_url: str) -> bytes:
        ...

