from app.analysis.application.internal.outboundservices.document_source_service import DocumentSourceService
from app.analysis.domain.model.valueobjects.source_document_reference import SourceDocumentReference
from app.documents.domain.repositories.document_repository import DocumentRepository


class DocumentSourceServiceImpl(DocumentSourceService):
    def __init__(self, document_repository: DocumentRepository) -> None:
        self._document_repository = document_repository

    async def get_document_reference(self, document_id: int) -> SourceDocumentReference | None:
        document = await self._document_repository.find_by_id(document_id)
        if document is None:
            return None

        return SourceDocumentReference(
            document_id=document.id or 0,
            original_filename=document.original_filename,
            mime_type=document.mime_type.value,
            document_url=document.storage_path.value,
        )

