from typing import Protocol

from app.documents.domain.model.commands.create_document_command import CreateDocumentCommand
from app.documents.shared.model.entities.document import Document


class DocumentCommandService(Protocol):
    async def handle_create_document(self, command: CreateDocumentCommand) -> Document:
        ...

    async def handle_update_document_status(self, document_id: int, status: str) -> Document | None:
        ...
