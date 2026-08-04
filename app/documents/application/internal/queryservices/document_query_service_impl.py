from app.documents.domain.model.queries.get_document_by_id_query import GetDocumentByIdQuery
from app.documents.domain.model.queries.list_documents_query import ListDocumentsQuery
from app.documents.domain.repositories.document_repository import DocumentRepository
from app.documents.domain.services.document_query_service import DocumentQueryService
from app.documents.domain.model.entities.document import Document


class DocumentQueryServiceImpl(DocumentQueryService):
    def __init__(self, document_repository: DocumentRepository) -> None:
        self._document_repository = document_repository

    async def handle_get_document_by_id(self, query: GetDocumentByIdQuery) -> Document | None:
        return await self._document_repository.find_by_id(query.document_id)

    async def handle_list_documents(self, query: ListDocumentsQuery) -> tuple[list[Document], int]:
        return await self._document_repository.list(query.page, query.page_size, query.owner_user_id)
