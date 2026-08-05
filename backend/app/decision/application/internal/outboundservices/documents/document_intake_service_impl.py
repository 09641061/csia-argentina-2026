from app.decision.application.internal.outboundservices.document_content_extractor import (
    DocumentContentExtractor,
)
from app.decision.application.internal.outboundservices.document_intake_service import (
    DocumentIntakeService,
    RegisteredDocument,
)
from app.decision.domain.exceptions import SecureQueryValidationError
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.documents.domain.exceptions import (
    DocumentFileTooLargeError,
    InvalidDocumentContentError,
    UnsupportedDocumentTypeError,
)
from app.documents.domain.model.commands.create_document_command import (
    CreateDocumentCommand,
)
from app.documents.domain.model.commands.record_document_review_outcome_command import (
    RecordDocumentReviewOutcomeCommand,
)
from app.documents.domain.model.queries.get_document_by_id_query import (
    GetDocumentByIdQuery,
)
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.services.document_command_service import (
    DocumentCommandService,
)
from app.documents.domain.services.document_query_service import DocumentQueryService


class DocumentIntakeServiceImpl(DocumentIntakeService):
    """
    Anti-corruption layer between Decision & Audit and Documents.

    Reading the allowed content back is done here, once the decision is ALLOWED,
    so the generator receives exactly the bytes that were reviewed.
    """

    def __init__(
        self,
        document_command_service: DocumentCommandService,
        document_query_service: DocumentQueryService,
        document_content_extractor: DocumentContentExtractor,
    ) -> None:
        self._document_command_service = document_command_service
        self._document_query_service = document_query_service
        self._document_content_extractor = document_content_extractor

    async def register_document(
        self,
        *,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> RegisteredDocument:
        try:
            document = await self._document_command_service.handle_create_document(
                CreateDocumentCommand(
                    original_filename=filename,
                    mime_type=mime_type,
                    content=content,
                )
            )
        except UnsupportedDocumentTypeError as error:
            raise SecureQueryValidationError(
                "Solo se admiten archivos JSON, PDF, DOCX, XLSX, PNG y JPEG."
            ) from error
        except DocumentFileTooLargeError as error:
            raise SecureQueryValidationError(
                "El documento supera el tamaño máximo permitido."
            ) from error
        except InvalidDocumentContentError as error:
            raise SecureQueryValidationError(
                "El archivo está vacío, dañado o no coincide con su formato declarado."
            ) from error

        return RegisteredDocument(
            document_id=document.id or 0,
            display_name=document.display_name.value,
        )

    async def read_allowed_document_content(
        self,
        document_id: int,
    ) -> dict[str, object] | list[object]:
        query = GetDocumentByIdQuery(document_id=document_id)
        document = await self._document_query_service.handle_get_document_by_id(query)
        if document is None:
            raise SecureQueryValidationError("El documento permitido ya no está disponible.")
        raw = await self._document_query_service.handle_read_document_content(
            query
        )
        return await self._document_content_extractor.extract_content(
            raw,
            document.mime_type.value,
            document.display_name.value,
        )

    async def record_review_outcome(
        self,
        *,
        document_id: int,
        decision: SecurityDecision,
        reason: str,
    ) -> None:
        status = (
            DocumentStatus.ANALYZED
            if decision == SecurityDecision.ALLOWED
            else DocumentStatus.BLOCKED
        )
        await self._document_command_service.handle_record_document_review_outcome(
            RecordDocumentReviewOutcomeCommand(
                document_id=document_id,
                status=status,
                blocked_reason=None if status == DocumentStatus.ANALYZED else reason,
            )
        )
