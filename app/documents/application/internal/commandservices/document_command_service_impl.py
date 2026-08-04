from datetime import UTC, datetime

from app.documents.domain.exceptions import DocumentFileTooLargeError, UnsupportedDocumentTypeError
from app.documents.domain.model.commands.create_document_command import CreateDocumentCommand
from app.documents.domain.model.commands.update_document_status_command import UpdateDocumentStatusCommand
from app.documents.domain.model.events.document_status_changed_event import DocumentStatusChangedEvent
from app.documents.domain.model.events.document_uploaded_event import DocumentUploadedEvent
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.repositories.document_repository import DocumentRepository
from app.documents.domain.services.document_command_service import DocumentCommandService
from app.documents.infrastructure.storage.local_document_storage import LocalDocumentStorage
from app.documents.shared.model.entities.document import Document


class DocumentCommandServiceImpl(DocumentCommandService):
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_storage: LocalDocumentStorage,
        allowed_mime_types: list[str],
        max_document_size_bytes: int,
    ) -> None:
        self._document_repository = document_repository
        self._document_storage = document_storage
        self._allowed_mime_types = allowed_mime_types
        self._max_document_size_bytes = max_document_size_bytes
        self.published_events: list[object] = []

    async def handle_create_document(self, command: CreateDocumentCommand) -> Document:
        self._validate_document_size(command.size_bytes)
        self._validate_mime_type(command.mime_type)

        storage_path = await self._document_storage.store(
            command.original_filename,
            command.content,
        )

        document = Document.create(
            owner_user_id=command.owner_user_id,
            name=command.name,
            original_filename=command.original_filename,
            mime_type=command.mime_type,
            size_bytes=command.size_bytes,
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

    def _validate_mime_type(self, mime_type: str) -> None:
        if mime_type not in self._allowed_mime_types:
            raise UnsupportedDocumentTypeError(f"Unsupported document type: {mime_type}")
