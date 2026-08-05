from app.analysis.application.internal.outboundservices.document_source_service import (
    DocumentSourceService,
)
from app.analysis.domain.exceptions import DocumentContentReadError
from app.analysis.domain.model.valueobjects.analyzed_document_source import (
    AnalyzedDocumentSource,
)
from app.documents.domain.exceptions import DocumentNotFoundError
from app.documents.domain.model.queries.get_document_by_id_query import GetDocumentByIdQuery
from app.documents.domain.services.document_query_service import DocumentQueryService
from app.documents.infrastructure.storage.exceptions import DocumentStorageError


class DocumentSourceServiceImpl(DocumentSourceService):
    """
    Anti-corruption layer between Analysis and Documents.

    It translates the Documents entity into the small, safe value object
    Analysis needs, and it reads content only through the Documents query
    service, so no storage detail crosses the boundary.
    """

    def __init__(self, document_query_service: DocumentQueryService) -> None:
        self._document_query_service = document_query_service

    async def get_document_source(self, document_id: int) -> AnalyzedDocumentSource | None:
        document = await self._document_query_service.handle_get_document_by_id(
            GetDocumentByIdQuery(document_id=document_id)
        )
        if document is None:
            return None

        return AnalyzedDocumentSource(
            document_id=document.id or 0,
            display_name=document.display_name.value,
            mime_type=document.mime_type.value,
            size_bytes=document.size_bytes.value,
        )

    async def read_document_content(self, document_id: int) -> bytes:
        try:
            return await self._document_query_service.handle_read_document_content(
                GetDocumentByIdQuery(document_id=document_id)
            )
        except DocumentNotFoundError as error:
            raise DocumentContentReadError("The registered document is not available") from error
        except DocumentStorageError as error:
            raise DocumentContentReadError(
                "The stored document content could not be read safely"
            ) from error
