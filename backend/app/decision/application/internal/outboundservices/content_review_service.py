from typing import Protocol

from app.decision.domain.model.valueobjects.reviewed_content_assessment import (
    ReviewedContentAssessment,
)


class ContentReviewService(Protocol):
    """
    Anti-corruption contract towards Analysis.

    Decision & Audit asks for a review and receives a small assessment value
    object. It never sees an Analysis entity, an Analysis SQLAlchemy model or
    the reviewed content itself.
    """

    async def review_prompt(self, prompt: str, requested_by: str) -> ReviewedContentAssessment: ...

    async def review_document(self, document_id: int) -> ReviewedContentAssessment: ...
