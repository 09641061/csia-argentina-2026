from app.decision.application.internal.outboundservices.document_content_extractor import (
    DocumentContentExtractor,
)
from app.decision.application.internal.outboundservices.document_intake_service import (
    DocumentIntakeService,
    RegisteredDocument,
)
from app.decision.domain.exceptions import SecureQueryValidationError
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.documents.interfaces.acl.documents_context_facade import (
    DocumentContextTooLargeError,
    DocumentsContextFacade,
    InvalidDocumentContextContentError,
    UnsupportedDocumentContextTypeError,
)


class DocumentIntakeServiceImpl(DocumentIntakeService):
    """
    Anti-corruption layer between Decision & Audit and Documents.

    Reading the allowed content back is done here, once the decision is ALLOWED,
    so the generator receives exactly the bytes that were reviewed.
    """

    def __init__(
        self,
        documents_facade: DocumentsContextFacade,
        document_content_extractor: DocumentContentExtractor,
    ) -> None:
        self._documents_facade = documents_facade
        self._document_content_extractor = document_content_extractor

    async def register_document(
        self,
        *,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> RegisteredDocument:
        try:
            document = await self._documents_facade.register_document(
                filename=filename,
                mime_type=mime_type,
                content=content,
            )
        except UnsupportedDocumentContextTypeError as error:
            raise SecureQueryValidationError(
                "Solo se admiten archivos JSON, PNG, JPEG y WebP."
            ) from error
        except DocumentContextTooLargeError as error:
            raise SecureQueryValidationError(
                "El documento supera el tamaño máximo permitido."
            ) from error
        except InvalidDocumentContextContentError as error:
            raise SecureQueryValidationError(
                "El archivo está vacío, dañado o no coincide con su formato declarado."
            ) from error

        return RegisteredDocument(
            document_id=int(document["document_id"]),
            display_name=str(document["display_name"]),
            attachment_url=(
                str(document["storage_url"])
                if document.get("storage_url") is not None
                else None
            ),
        )

    async def read_allowed_document_content(
        self,
        document_id: int,
    ) -> dict[str, object] | list[object]:
        document = await self._documents_facade.find_document(document_id)
        if document is None:
            raise SecureQueryValidationError("El documento permitido ya no está disponible.")
        raw = await self._documents_facade.read_document_content(document_id)
        return await self._document_content_extractor.extract_content(
            raw,
            str(document["mime_type"]),
            str(document["display_name"]),
        )

    async def record_review_outcome(
        self,
        *,
        document_id: int,
        decision: SecurityDecision,
        reason: str,
    ) -> None:
        status = (
            "analyzed"
            if decision == SecurityDecision.ALLOWED
            else "blocked"
        )
        await self._documents_facade.record_review_outcome(
            document_id=document_id,
            status=status,
            blocked_reason=None if status == "analyzed" else reason,
        )
