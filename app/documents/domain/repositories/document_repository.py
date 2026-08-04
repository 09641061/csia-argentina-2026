from typing import Protocol

from app.documents.shared.model.entities.document import Document


class DocumentRepository(Protocol):
    async def save(self, document: Document) -> Document:
        ...

    async def find_by_id(self, document_id: int) -> Document | None:
        ...

    async def list(self, page: int, page_size: int, owner_user_id: int | None = None) -> tuple[list[Document], int]:
        ...
