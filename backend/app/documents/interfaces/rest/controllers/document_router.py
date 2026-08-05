from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.settings import get_settings
from app.documents.application.internal.commandservices.document_command_service_impl import (
    DocumentCommandServiceImpl,
)
from app.documents.application.internal.queryservices.document_query_service_impl import (
    DocumentQueryServiceImpl,
)
from app.documents.domain.exceptions import (
    DocumentFileTooLargeError,
    InvalidDocumentContentError,
    UnsupportedDocumentTypeError,
)
from app.documents.domain.model.commands.create_document_command import (
    CreateDocumentCommand,
)
from app.documents.domain.model.entities.document import Document
from app.documents.domain.model.queries.get_document_by_id_query import (
    GetDocumentByIdQuery,
)
from app.documents.domain.model.queries.get_document_table_query import GetDocumentTableQuery
from app.documents.domain.model.queries.list_documents_query import ListDocumentsQuery
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)
from app.documents.infrastructure.storage.document_storage_provider import (
    get_document_storage,
)
from app.documents.infrastructure.storage.exceptions import (
    DocumentStorageNotConfiguredError,
    DocumentStorageUploadError,
)
from app.documents.interfaces.rest.resources.create_document_response import (
    CreateDocumentResponse,
)
from app.documents.interfaces.rest.resources.document_resource import DocumentResource
from app.documents.interfaces.rest.resources.document_table_response import DocumentTableResponse
from app.documents.interfaces.rest.resources.list_documents_response import (
    DocumentPageMetadataResponse,
    ListDocumentsResponse,
)
from app.shared.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.iam.interfaces.rest.controllers.authentication_router import (
    require_authenticated_user,
)

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
    dependencies=[Depends(require_authenticated_user)],
    responses={401: {"description": "Authentication required"}},
)


async def get_document_command_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentCommandServiceImpl:
    settings = get_settings()
    try:
        storage = get_document_storage()
    except DocumentStorageNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is not configured",
        ) from error
    return DocumentCommandServiceImpl(
        document_repository=SqlAlchemyDocumentRepository(session),
        document_storage=storage,
        max_document_size_bytes=settings.max_document_size_bytes,
    )


async def get_document_query_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentQueryServiceImpl:
    return DocumentQueryServiceImpl(
        document_repository=SqlAlchemyDocumentRepository(session),
        document_storage=get_document_storage(),
    )


def to_document_resource(document: Document) -> DocumentResource:
    return DocumentResource(
        id=document.id or 0,
        display_name=document.display_name.value,
        mime_type=document.mime_type.value,
        size_bytes=document.size_bytes.value,
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
    summary="Register a supported document",
    description=(
        "Receives a JSON, PNG or JPEG file, validates its real container, "
        "stores it in the configured private storage and registers its metadata. "
        "The declared MIME type is not trusted: the bytes themselves are inspected."
    ),
    responses={
        201: {"description": "Document registered successfully"},
        400: {"description": "Empty, malformed or mismatched document content"},
        413: {"description": "Document exceeds the maximum allowed size"},
        415: {"description": "Unsupported document type"},
        503: {"description": "Document storage is unavailable"},
    },
)
async def create_document(
    file: Annotated[UploadFile, File(description="JSON, PNG or JPEG file")],
    command_service: Annotated[DocumentCommandServiceImpl, Depends(get_document_command_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateDocumentResponse:
    settings = get_settings()
    content = await file.read()
    if len(content) > settings.max_document_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Document size exceeds the limit of {settings.max_document_size_mb} MB",
        )

    unit_of_work = SqlAlchemyUnitOfWork(session)
    try:
        document = await command_service.handle_create_document(
            CreateDocumentCommand(
                original_filename=file.filename or "document.json",
                mime_type=file.content_type or "application/octet-stream",
                content=content,
            )
        )
        await unit_of_work.commit()
    except UnsupportedDocumentTypeError as error:
        await unit_of_work.rollback()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(error)
        ) from error
    except DocumentFileTooLargeError as error:
        await unit_of_work.rollback()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(error)
        ) from error
    except (InvalidDocumentContentError, ValueError) as error:
        await unit_of_work.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except DocumentStorageUploadError as error:
        await unit_of_work.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The document could not be stored",
        ) from error

    return CreateDocumentResponse(**to_document_resource(document).model_dump())


@router.get(
    "",
    response_model=ListDocumentsResponse,
    summary="List registered documents",
    description="Returns registered documents in reverse creation order with bounded pagination.",
    responses={
        200: {"description": "Documents returned successfully"},
        400: {"description": "Invalid pagination"},
    },
)
async def list_documents(
    query_service: Annotated[DocumentQueryServiceImpl, Depends(get_document_query_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Documents per page")] = 20,
) -> ListDocumentsResponse:
    try:
        documents, total = await query_service.handle_list_documents(
            ListDocumentsQuery(page=page, page_size=page_size)
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return ListDocumentsResponse(
        items=[to_document_resource(document) for document in documents],
        page=DocumentPageMetadataResponse(page=page, page_size=page_size, total=total),
    )


@router.get(
    "/{document_id}/table",
    response_model=DocumentTableResponse,
    summary="Get normalized JSON table data",
    description="Extracts a stored JSON document into columns, rows and scalar metadata suitable for frontend table rendering.",
    responses={
        200: {"description": "Normalized table returned"},
        400: {"description": "The document is not JSON or its identifier is invalid"},
        401: {"description": "Authentication required"},
        404: {"description": "Document not found"},
    },
)
async def get_document_table(
    document_id: int,
    query_service: Annotated[DocumentQueryServiceImpl, Depends(get_document_query_service)],
) -> DocumentTableResponse:
    try:
        table = await query_service.handle_get_document_table(
            GetDocumentTableQuery(document_id=document_id)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    if table is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return DocumentTableResponse(
        document_id=document_id,
        columns=list(table.columns),
        rows=list(table.rows),
        metadata=table.metadata,
        total_rows=len(table.rows),
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResource,
    summary="Get a document by ID",
    description="Retrieves the public metadata of a registered document.",
    responses={
        200: {"description": "Document found"},
        400: {"description": "Invalid document identifier"},
        404: {"description": "Document not found"},
    },
)
async def get_document_by_id(
    document_id: int,
    query_service: Annotated[DocumentQueryServiceImpl, Depends(get_document_query_service)],
) -> DocumentResource:
    try:
        document = await query_service.handle_get_document_by_id(
            GetDocumentByIdQuery(document_id=document_id)
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return to_document_resource(document)
