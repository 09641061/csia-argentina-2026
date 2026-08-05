from app.documents.application.internal.outboundservices.document_storage import DocumentStorage
from app.documents.domain.exceptions import DocumentNotFoundError
from app.documents.domain.model.entities.document import Document
from app.documents.domain.model.queries.get_document_by_id_query import GetDocumentByIdQuery
from app.documents.domain.model.queries.list_documents_query import ListDocumentsQuery
from app.documents.domain.repositories.document_repository import DocumentRepository
from app.documents.domain.services.document_query_service import DocumentQueryService


class DocumentQueryServiceImpl(DocumentQueryService):
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_storage: DocumentStorage | None = None,
    ) -> None:
        self._document_repository = document_repository
        self._document_storage = document_storage

    async def handle_get_document_by_id(self, query: GetDocumentByIdQuery) -> Document | None:
        return await self._document_repository.find_by_id(query.document_id)

    async def handle_list_documents(
        self,
        query: ListDocumentsQuery,
    ) -> tuple[list[Document], int]:
        return await self._document_repository.list(query.page, query.page_size)

    async def handle_read_document_content(self, query: GetDocumentByIdQuery) -> bytes:
        """
        Return the stored bytes of a registered document.

        This is the only way another bounded context can reach the content: it
        goes through the storage adapter using an internal reference, never
        through a URL supplied from outside.
        """

        if self._document_storage is None:
            raise DocumentNotFoundError("Document content is not readable in this context")
        document = await self._document_repository.find_by_id(query.document_id)
        if document is None:
            raise DocumentNotFoundError("Document not found")
        return await self._document_storage.read(document.storage_reference)
