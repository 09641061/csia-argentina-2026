from app.documents.domain.model.commands.create_document_command import CreateDocumentCommand
from app.documents.domain.model.commands.record_document_review_outcome_command import (
    RecordDocumentReviewOutcomeCommand,
)
from app.documents.domain.model.queries.get_document_by_id_query import GetDocumentByIdQuery
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.exceptions import (
    DocumentFileTooLargeError,
    InvalidDocumentContentError,
    UnsupportedDocumentTypeError,
)
from app.documents.domain.services.document_command_service import DocumentCommandService
from app.documents.domain.services.document_query_service import DocumentQueryService
from app.documents.infrastructure.storage.exceptions import DocumentStorageError
from app.documents.interfaces.acl.documents_context_facade import (
    DocumentsContextError,
    DocumentsContextFacade,
    DocumentContextTooLargeError,
    InvalidDocumentContextContentError,
    UnsupportedDocumentContextTypeError,
)


class DocumentsContextFacadeImpl(DocumentsContextFacade):
    def __init__(
        self,
        command_service: DocumentCommandService,
        query_service: DocumentQueryService,
    ) -> None:
        self._command_service = command_service
        self._query_service = query_service

    async def register_document(
        self, *, filename: str, mime_type: str, content: bytes
    ) -> dict[str, object]:
        try:
            document = await self._command_service.handle_create_document(
                CreateDocumentCommand(
                    original_filename=filename,
                    mime_type=mime_type,
                    content=content,
                )
            )
        except UnsupportedDocumentTypeError as error:
            raise UnsupportedDocumentContextTypeError("Unsupported document type") from error
        except DocumentFileTooLargeError as error:
            raise DocumentContextTooLargeError("Document is too large") from error
        except InvalidDocumentContentError as error:
            raise InvalidDocumentContextContentError("Invalid document content") from error
        return {
            "document_id": document.id or 0,
            "display_name": document.display_name.value,
            "mime_type": document.mime_type.value,
            "size_bytes": document.size_bytes.value,
        }

    async def find_document(self, document_id: int) -> dict[str, object] | None:
        document = await self._query_service.handle_get_document_by_id(
            GetDocumentByIdQuery(document_id=document_id)
        )
        if document is None:
            return None
        return {
            "document_id": document.id or 0,
            "display_name": document.display_name.value,
            "mime_type": document.mime_type.value,
            "size_bytes": document.size_bytes.value,
        }

    async def read_document_content(self, document_id: int) -> bytes:
        try:
            return await self._query_service.handle_read_document_content(
                GetDocumentByIdQuery(document_id=document_id)
            )
        except (ValueError, DocumentStorageError) as error:
            raise DocumentsContextError("Document content is unavailable") from error

    async def record_review_outcome(
        self, *, document_id: int, status: str, blocked_reason: str | None
    ) -> None:
        await self._command_service.handle_record_document_review_outcome(
            RecordDocumentReviewOutcomeCommand(
                document_id=document_id,
                status=DocumentStatus(status),
                blocked_reason=blocked_reason,
            )
        )
