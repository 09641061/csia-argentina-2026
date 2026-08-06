from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.domain.model.entities.document import Document
from app.documents.domain.model.valueobjects.document_display_name import DocumentDisplayName
from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType
from app.documents.domain.model.valueobjects.document_size_bytes import DocumentSizeBytes
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.model.valueobjects.document_storage_reference import (
    DocumentStorageReference,
)
from app.documents.domain.repositories.document_repository import DocumentRepository
from app.documents.infrastructure.persistence.sqlalchemy.models.document_model import DocumentModel


class SqlAlchemyDocumentRepository(DocumentRepository):
    """
    Stages document changes on the session.

    Committing belongs to the application service through the unit of work, so
    an upload and the audit record written for it land together or not at all.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, document: Document) -> Document:
        model: DocumentModel | None = None
        if document.id is not None:
            model = await self._session.scalar(
                select(DocumentModel).where(DocumentModel.id == document.id)
            )
            if model is None:
                raise ValueError("Document not found")

        if model is None:
            model = DocumentModel(
                display_name=document.display_name.value,
                mime_type=document.mime_type.value,
                size_bytes=document.size_bytes.value,
                storage_reference=document.storage_reference.value,
                status=document.status.value,
                blocked_reason=document.blocked_reason,
                created_at=document.created_at,
                updated_at=document.updated_at,
                analyzed_at=document.analyzed_at,
            )
            self._session.add(model)
        else:
            model.display_name = document.display_name.value
            model.mime_type = document.mime_type.value
            model.size_bytes = document.size_bytes.value
            model.storage_reference = document.storage_reference.value
            model.status = document.status.value
            model.blocked_reason = document.blocked_reason
            model.updated_at = document.updated_at
            model.analyzed_at = document.analyzed_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def find_by_id(self, document_id: int) -> Document | None:
        model = await self._session.scalar(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        return self._to_domain(model) if model is not None else None

    async def list(self, page: int, page_size: int) -> tuple[list[Document], int]:
        total = await self._session.scalar(select(func.count(DocumentModel.id)))
        result = await self._session.execute(
            select(DocumentModel)
            .order_by(DocumentModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [self._to_domain(model) for model in result.scalars().all()], int(total or 0)

    def _to_domain(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            display_name=DocumentDisplayName(model.display_name),
            mime_type=DocumentMimeType(model.mime_type),
            size_bytes=DocumentSizeBytes(model.size_bytes),
            storage_reference=DocumentStorageReference(model.storage_reference),
            status=DocumentStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            analyzed_at=model.analyzed_at,
            blocked_reason=model.blocked_reason,
        )
