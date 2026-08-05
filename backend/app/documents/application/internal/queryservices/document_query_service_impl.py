import json

from app.documents.application.internal.outboundservices.document_storage import DocumentStorage
from app.documents.domain.exceptions import DocumentNotFoundError
from app.documents.domain.model.entities.document import Document
from app.documents.domain.model.queries.get_document_by_id_query import GetDocumentByIdQuery
from app.documents.domain.model.queries.get_document_table_query import GetDocumentTableQuery
from app.documents.domain.model.queries.list_documents_query import ListDocumentsQuery
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType
from app.documents.domain.model.valueobjects.tabular_document_content import (
    TableCell,
    TabularDocumentContent,
)
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

    async def handle_get_document_table(
        self, query: GetDocumentTableQuery
    ) -> TabularDocumentContent | None:
        document = await self._document_repository.find_by_id(query.document_id)
        if document is None:
            return None
        if document.mime_type.value != DocumentMimeType.JSON:
            raise ValueError("Only JSON documents can be represented as a table")
        content = await self.handle_read_document_content(
            GetDocumentByIdQuery(document_id=query.document_id)
        )
        parsed = json.loads(content.decode("utf-8"))
        metadata: dict[str, TableCell] = {}
        records: list[dict[str, object]]
        if isinstance(parsed, list):
            records = [item for item in parsed if isinstance(item, dict)]
            if len(records) != len(parsed):
                records = [{"value": item} for item in parsed]
        else:
            list_fields = [
                (key, value)
                for key, value in parsed.items()
                if isinstance(value, list) and all(isinstance(item, dict) for item in value)
            ]
            if list_fields:
                selected_key, selected_records = max(list_fields, key=lambda item: len(item[1]))
                records = selected_records
                metadata = {
                    key: self._to_table_cell(value)
                    for key, value in parsed.items()
                    if key != selected_key
                }
            else:
                records = [parsed]
        columns = tuple(dict.fromkeys(key for record in records for key in record))
        if not columns:
            columns = ("value",)
            records = [{"value": None}]
        rows = tuple(
            {column: self._to_table_cell(record.get(column)) for column in columns}
            for record in records
        )
        return TabularDocumentContent(columns=columns, rows=rows, metadata=metadata)

    @staticmethod
    def _to_table_cell(value: object) -> TableCell:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
