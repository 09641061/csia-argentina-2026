from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.database import get_session
from app.core.settings import get_settings
from app.documents.application.internal.commandservices.document_command_service_impl import (
    DocumentCommandServiceImpl,
)
from app.documents.application.internal.queryservices.document_query_service_impl import (
    DocumentQueryServiceImpl,
)
from app.documents.domain.exceptions import DocumentFileTooLargeError, UnsupportedDocumentTypeError
from app.documents.domain.model.commands.create_document_command import CreateDocumentCommand
from app.documents.domain.model.queries.get_document_by_id_query import GetDocumentByIdQuery
from app.documents.domain.model.queries.list_documents_query import ListDocumentsQuery
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)
from app.documents.infrastructure.storage.cloudinary_document_storage import CloudinaryDocumentStorage
from app.documents.infrastructure.storage.exceptions import DocumentStorageUploadError
from app.documents.interfaces.rest.resources.create_document_response import CreateDocumentResponse
from app.documents.interfaces.rest.resources.document_resource import DocumentResource
from app.documents.interfaces.rest.resources.list_documents_response import ListDocumentsResponse, DocumentPageMetadataResponse

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


async def get_document_command_service(
    session=Depends(get_session),
) -> DocumentCommandServiceImpl:
    settings = get_settings()
    repository = SqlAlchemyDocumentRepository(session)
    storage = CloudinaryDocumentStorage()
    return DocumentCommandServiceImpl(
        document_repository=repository,
        document_storage=storage,
        allowed_mime_types=settings.allowed_mime_type_list,
        max_document_size_bytes=settings.max_document_size_bytes,
    )


async def get_document_query_service(session=Depends(get_session)) -> DocumentQueryServiceImpl:
    repository = SqlAlchemyDocumentRepository(session)
    return DocumentQueryServiceImpl(document_repository=repository)


def _to_document_resource(document) -> DocumentResource:
    return DocumentResource(
        id=document.id or 0,
        owner_user_id=document.owner_user_id,
        name=document.name.value,
        original_filename=document.original_filename,
        mime_type=document.mime_type.value,
        size_bytes=document.size_bytes.value,
        storage_path=document.storage_path.value,
        status=document.status.value,
        created_at=document.created_at,
        updated_at=document.updated_at,
        analyzed_at=document.analyzed_at,
        blocked_reason=document.blocked_reason,
    )


@router.post(
    "",
    response_model=CreateDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Receives a document file, validates it, stores it in Cloudinary, and registers it in PostgreSQL.",
    responses={
        201: {"description": "Document uploaded successfully"},
        400: {"description": "Invalid document or business rule violation"},
        502: {"description": "Cloud storage upload failed"},
    },
)
async def create_document(
    name: Annotated[str, Form(description="Business document name", min_length=1, max_length=255)],
    owner_user_id: Annotated[int, Form(description="Owner user identifier", gt=0)],
    file: Annotated[UploadFile, File(description="Document file to upload")],
    command_service: Annotated[DocumentCommandServiceImpl, Depends(get_document_command_service)],
) -> CreateDocumentResponse:
    content = await file.read()

    try:
        command = CreateDocumentCommand(
            owner_user_id=owner_user_id,
            name=name,
            original_filename=file.filename or "document",
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            content=content,
        )
        document = await command_service.handle_create_document(command)
    except (ValueError, DocumentFileTooLargeError, UnsupportedDocumentTypeError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except DocumentStorageUploadError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    return _to_document_resource(document)


@router.get(
    "/{document_id}",
    response_model=DocumentResource,
    status_code=status.HTTP_200_OK,
    summary="Get a document by ID",
    description="Retrieves a registered document by its identifier.",
    responses={
        200: {"description": "Document found"},
        404: {"description": "Document not found"},
    },
)
async def get_document_by_id(
    document_id: int,
    query_service: Annotated[DocumentQueryServiceImpl, Depends(get_document_query_service)],
) -> DocumentResource:
    try:
        query = GetDocumentByIdQuery(document_id=document_id)
        document = await query_service.handle_get_document_by_id(query)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return _to_document_resource(document)


@router.get(
    "",
    response_model=ListDocumentsResponse,
    status_code=status.HTTP_200_OK,
    summary="List documents",
    description="Returns a paginated list of documents.",
    responses={
        200: {"description": "Documents returned successfully"},
    },
)
async def list_documents(
    query_service: Annotated[DocumentQueryServiceImpl, Depends(get_document_query_service)],
    page: int = 1,
    page_size: int = 20,
    owner_user_id: int | None = None,
) -> ListDocumentsResponse:
    try:
        query = ListDocumentsQuery(page=page, page_size=page_size, owner_user_id=owner_user_id)
        documents, total = await query_service.handle_list_documents(query)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return ListDocumentsResponse(
        items=[_to_document_resource(document) for document in documents],
        page=DocumentPageMetadataResponse(page=page, page_size=page_size, total=total),
    )
