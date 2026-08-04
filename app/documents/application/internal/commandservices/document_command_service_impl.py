from datetime import UTC, datetime

from app.documents.domain.exceptions import DocumentFileTooLargeError
from app.documents.domain.model.commands.create_document_command import CreateDocumentCommand
from app.documents.domain.model.commands.update_document_status_command import UpdateDocumentStatusCommand
from app.documents.domain.model.events.document_status_changed_event import DocumentStatusChangedEvent
from app.documents.domain.model.events.document_uploaded_event import DocumentUploadedEvent
from app.documents.domain.model.entities.document import Document
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.model.valueobjects.json_document_content import JsonDocumentContent
from app.documents.domain.repositories.document_repository import DocumentRepository
from app.documents.domain.services.document_command_service import DocumentCommandService
from app.documents.infrastructure.storage.cloudinary_document_storage import CloudinaryDocumentStorage


class DocumentCommandServiceImpl(DocumentCommandService):
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_storage: CloudinaryDocumentStorage,
        max_document_size_bytes: int,
    ) -> None:
        self._document_repository = document_repository
        self._document_storage = document_storage
        self._max_document_size_bytes = max_document_size_bytes
        self.published_events: list[object] = []

    async def handle_create_document(self, command: CreateDocumentCommand) -> Document:
        self._validate_document_size(command.size_bytes)
        mime_type = DocumentMimeType(command.mime_type)
        content = JsonDocumentContent(command.content)

        storage_path = await self._document_storage.store(
            command.original_filename,
            content.value,
            mime_type.value,
        )

        document = Document.create(
            owner_user_id=command.owner_user_id,
            name=command.name,
            original_filename=command.original_filename,
            mime_type=mime_type.value,
            size_bytes=content.size_bytes,
            storage_path=storage_path,
        )

        saved_document = await self._document_repository.save(document)
        self.published_events.append(
            DocumentUploadedEvent(
                document_id=saved_document.id or 0,
                owner_user_id=saved_document.owner_user_id,
            )
        )
        return saved_document

    async def handle_update_document_status(
        self,
        document_id: int,
        status: str,
    ) -> Document | None:
        document = await self._document_repository.find_by_id(document_id)
        if document is None:
            return None

        document.status = DocumentStatus(status)
        document.updated_at = datetime.now(UTC)

        if document.status == DocumentStatus.BLOCKED and document.blocked_reason is None:
            document.blocked_reason = "Document blocked by policy"

        saved_document = await self._document_repository.save(document)
        self.published_events.append(
            DocumentStatusChangedEvent(
                document_id=saved_document.id or 0,
                new_status=saved_document.status,
            )
        )
        return saved_document

    def _validate_document_size(self, size_bytes: int) -> None:
        if size_bytes > self._max_document_size_bytes:
            raise DocumentFileTooLargeError(
                f"Document size exceeds the limit of {self._max_document_size_bytes} bytes"
            )

