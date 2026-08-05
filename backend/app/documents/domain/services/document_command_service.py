from typing import Protocol

from app.documents.domain.model.commands.create_document_command import CreateDocumentCommand
from app.documents.domain.model.commands.record_document_review_outcome_command import (
    RecordDocumentReviewOutcomeCommand,
)
from app.documents.domain.model.entities.document import Document


class DocumentCommandService(Protocol):
    async def handle_create_document(self, command: CreateDocumentCommand) -> Document: ...

    async def handle_record_document_review_outcome(
        self,
        command: RecordDocumentReviewOutcomeCommand,
    ) -> Document | None: ...
