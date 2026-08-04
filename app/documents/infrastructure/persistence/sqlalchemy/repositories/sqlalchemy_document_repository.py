from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.domain.model.valueobjects.document_mime_type import DocumentMimeType
from app.documents.domain.model.valueobjects.document_name import DocumentName
from app.documents.domain.model.valueobjects.document_size_bytes import DocumentSizeBytes
from app.documents.domain.model.valueobjects.document_status import DocumentStatus
from app.documents.domain.model.valueobjects.document_storage_path import DocumentStoragePath
from app.documents.domain.repositories.document_repository import DocumentRepository
from app.documents.infrastructure.persistence.sqlalchemy.models.document_model import DocumentModel
from app.documents.shared.model.entities.document import Document


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, document: Document) -> Document:
        if document.id is None:
            model = DocumentModel(
                owner_user_id=document.owner_user_id,
                name=document.name.value,
                original_filename=document.original_filename,
                mime_type=document.mime_type.value,
                size_bytes=document.size_bytes.value,
                storage_path=document.storage_path.value,
                status=document.status.value,
                blocked_reason=document.blocked_reason,
                created_at=document.created_at,
                updated_at=document.updated_at,
                analyzed_at=document.analyzed_at,
            )
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            await self._session.commit()
            return self._to_domain(model)

        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Document not found")

        model.owner_user_id = document.owner_user_id
        model.name = document.name.value
        model.original_filename = document.original_filename
        model.mime_type = document.mime_type.value
        model.size_bytes = document.size_bytes.value
        model.storage_path = document.storage_path.value
        model.status = document.status.value
        model.blocked_reason = document.blocked_reason
        model.created_at = document.created_at
        model.updated_at = document.updated_at
        model.analyzed_at = document.analyzed_at

        await self._session.flush()
        await self._session.refresh(model)
        await self._session.commit()
        return self._to_domain(model)

    async def find_by_id(self, document_id: int) -> Document | None:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def list(
        self,
        page: int,
        page_size: int,
        owner_user_id: int | None = None,
    ) -> tuple[list[Document], int]:
        statement = select(DocumentModel)
        count_statement = select(func.count(DocumentModel.id))
        if owner_user_id is not None:
            statement = statement.where(DocumentModel.owner_user_id == owner_user_id)
            count_statement = count_statement.where(DocumentModel.owner_user_id == owner_user_id)

        total = await self._session.scalar(count_statement)
        total_records = int(total or 0)

        result = await self._session.execute(
            statement.order_by(DocumentModel.id.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        models = list(result.scalars().all())
        return [self._to_domain(model) for model in models], total_records

    def _to_domain(self, model: DocumentModel) -> Document:
        document = Document(
            id=model.id,
            owner_user_id=model.owner_user_id,
            name=DocumentName(model.name),
            original_filename=model.original_filename,
            mime_type=DocumentMimeType(model.mime_type),
            size_bytes=DocumentSizeBytes(model.size_bytes),
            storage_path=DocumentStoragePath(model.storage_path),
            status=DocumentStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            analyzed_at=model.analyzed_at,
            blocked_reason=model.blocked_reason,
        )
        return document
