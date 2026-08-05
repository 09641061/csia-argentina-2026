from typing import Protocol


class DocumentStorage(Protocol):
    async def store(self, original_filename: str, content: bytes, content_type: str) -> str:
        ...
