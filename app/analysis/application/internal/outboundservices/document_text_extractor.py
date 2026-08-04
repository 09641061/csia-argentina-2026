from typing import Protocol


class DocumentTextExtractor(Protocol):
    def extract_text(self, content: bytes, mime_type: str, original_filename: str) -> str:
        ...

