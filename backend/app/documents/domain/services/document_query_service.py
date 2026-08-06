from typing import Protocol

from app.documents.domain.model.entities.document import Document
from app.documents.domain.model.queries.get_document_by_id_query import GetDocumentByIdQuery
from app.documents.domain.model.queries.get_document_table_query import GetDocumentTableQuery
from app.documents.domain.model.queries.list_documents_query import ListDocumentsQuery
from app.documents.domain.model.valueobjects.tabular_document_content import TabularDocumentContent


class DocumentQueryService(Protocol):
    async def handle_get_document_by_id(
        self,
        query: GetDocumentByIdQuery,
    ) -> Document | None: ...

    async def handle_list_documents(
        self,
        query: ListDocumentsQuery,
    ) -> tuple[list[Document], int]: ...

    async def handle_read_document_content(self, query: GetDocumentByIdQuery) -> bytes: ...

    async def handle_get_document_table(
        self, query: GetDocumentTableQuery
    ) -> TabularDocumentContent | None: ...
