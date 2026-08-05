from app.analysis.application.internal.outboundservices.document_source_service import (
    DocumentSourceService,
)
from app.analysis.domain.exceptions import DocumentContentReadError
from app.analysis.domain.model.valueobjects.analyzed_document_source import (
    AnalyzedDocumentSource,
)
from app.documents.interfaces.acl.documents_context_facade import (
    DocumentsContextError,
    DocumentsContextFacade,
)


class DocumentSourceServiceImpl(DocumentSourceService):
    """
    Anti-corruption layer between Analysis and Documents.

    It translates the Documents entity into the small, safe value object
    Analysis needs, and it reads content only through the Documents query
    service, so no storage detail crosses the boundary.
    """

    def __init__(self, documents_facade: DocumentsContextFacade) -> None:
        self._documents_facade = documents_facade

    async def get_document_source(self, document_id: int) -> AnalyzedDocumentSource | None:
        document = await self._documents_facade.find_document(document_id)
        if document is None:
            return None

        return AnalyzedDocumentSource(
            document_id=int(document["document_id"]),
            display_name=str(document["display_name"]),
            mime_type=str(document["mime_type"]),
            size_bytes=int(document["size_bytes"]),
        )

    async def read_document_content(self, document_id: int) -> bytes:
        try:
            return await self._documents_facade.read_document_content(document_id)
        except DocumentsContextError as error:
            raise DocumentContentReadError(
                "The stored document content could not be read safely"
            ) from error
