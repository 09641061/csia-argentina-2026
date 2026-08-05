from app.documents.application.internal.outboundservices.document_storage import (
    DocumentStorage,
)
from app.documents.domain.exceptions import DocumentFileTooLargeError
from app.documents.domain.model.commands.create_document_command import (
    CreateDocumentCommand,
)
from app.documents.domain.model.commands.record_document_review_outcome_command import (
    RecordDocumentReviewOutcomeCommand,
)
from app.documents.domain.model.entities.document import Document
from app.documents.domain.model.events.document_status_changed_event import (
    DocumentStatusChangedEvent,
)
from app.documents.domain.model.events.document_uploaded_event import (
    DocumentUploadedEvent,
)
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.model.valueobjects.supported_document_content import (
    SupportedDocumentContent,
)
from app.documents.domain.repositories.document_repository import DocumentRepository
from app.documents.domain.services.document_command_service import (
    DocumentCommandService,
)


class DocumentCommandServiceImpl(DocumentCommandService):
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_storage: DocumentStorage,
        max_document_size_bytes: int,
    ) -> None:
        self._document_repository = document_repository
        self._document_storage = document_storage
        self._max_document_size_bytes = max_document_size_bytes
        self.published_events: list[object] = []

    async def handle_create_document(self, command: CreateDocumentCommand) -> Document:
        self._validate_document_size(command.size_bytes)
        mime_type = DocumentMimeType.from_upload(
            command.mime_type, command.original_filename
        )
        content = SupportedDocumentContent(command.content, mime_type)

        storage_reference = await self._document_storage.store(content.value, mime_type.value)

        document = Document.register(
            original_filename=command.original_filename,
            mime_type=mime_type.value,
            size_bytes=content.size_bytes,
            storage_reference=storage_reference,
        )

        saved_document = await self._document_repository.save(document)
        self.published_events.append(DocumentUploadedEvent(document_id=saved_document.id or 0))
        return saved_document

    async def handle_record_document_review_outcome(
        self,
        command: RecordDocumentReviewOutcomeCommand,
    ) -> Document | None:
        document = await self._document_repository.find_by_id(command.document_id)
        if document is None:
            return None

        if command.status == DocumentStatus.BLOCKED:
            document.mark_blocked(command.blocked_reason or "Document blocked by policy")
        elif command.status == DocumentStatus.ANALYZED:
            document.mark_analyzed()
        elif command.status == DocumentStatus.PROCESSING:
            document.mark_processing()
        else:
            raise ValueError("Unsupported document review outcome")

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
