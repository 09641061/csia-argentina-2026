from app.analysis.application.internal.outboundservices.document_source_service import (
    DocumentSourceService,
)
from app.analysis.domain.model.valueobjects.source_document_reference import (
    SourceDocumentReference,
)
from app.documents.domain.model.queries.get_document_by_id_query import (
    GetDocumentByIdQuery,
)
from app.documents.domain.services.document_query_service import DocumentQueryService


class DocumentSourceServiceImpl(DocumentSourceService):
    def __init__(self, document_query_service: DocumentQueryService) -> None:
        self._document_query_service = document_query_service

    async def get_document_reference(
        self, document_id: int
    ) -> SourceDocumentReference | None:
        document = await self._document_query_service.handle_get_document_by_id(
            GetDocumentByIdQuery(document_id=document_id)
        )
        if document is None:
            return None

        return SourceDocumentReference(
            document_id=document.id or 0,
            original_filename=document.original_filename,
            mime_type=document.mime_type.value,
            document_url=document.storage_path.value,
            size_bytes=document.size_bytes.value,
        )
