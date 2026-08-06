from typing import Protocol


class AnalysisContextFacade(Protocol):
    async def review_prompt(self, prompt: str, requested_by: str) -> dict[str, object | None]: ...

    async def review_document(self, document_id: int) -> dict[str, object | None]: ...
