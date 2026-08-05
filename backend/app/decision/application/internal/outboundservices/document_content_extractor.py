from typing import Protocol


class DocumentContentExtractor(Protocol):
    """Decision-facing contract for reading an already reviewed attachment."""

    async def extract_content(
        self, content: bytes, mime_type: str, original_filename: str
    ) -> dict[str, object] | list[object]: ...
