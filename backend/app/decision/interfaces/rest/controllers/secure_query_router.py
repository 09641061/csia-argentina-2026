from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.composition import (
    build_secure_interaction_query_service,
    build_secure_query_command_service,
)
from app.core.database import get_session
from app.core.settings import get_settings
from app.decision.application.internal.commandservices.submit_secure_query_command_service_impl import (
    SecureQueryResult,
    SubmitSecureQueryCommandServiceImpl,
)
from app.decision.application.internal.queryservices.secure_interaction_query_service_impl import (
    SecureInteractionQueryServiceImpl,
)
from app.decision.domain.exceptions import SecureQueryValidationError
from app.decision.domain.model.commands.submit_secure_query_command import (
    SubmitSecureQueryCommand,
)
from app.decision.domain.model.entities.secure_interaction import SecureInteraction
from app.decision.domain.model.queries.get_secure_interaction_by_id_query import (
    GetSecureInteractionByIdQuery,
)
from app.decision.domain.model.queries.list_secure_interactions_query import (
    ListSecureInteractionsQuery,
)
from app.decision.interfaces.rest.resources.secure_interaction_list_response import (
    SecureInteractionListResponse,
    SecureInteractionPageMetadataResponse,
)
from app.decision.interfaces.rest.resources.secure_interaction_resource import (
    MaskedFindingResource,
    SecureInteractionResource,
)
from app.decision.interfaces.rest.resources.secure_query_response import (
    AssistantAnswerResource,
    SecureQueryResponse,
)
from app.shared.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(prefix="/api/v1", tags=["Secure queries"])


async def get_secure_query_command_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SubmitSecureQueryCommandServiceImpl:
    return build_secure_query_command_service(session)


async def get_secure_interaction_query_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecureInteractionQueryServiceImpl:
    return build_secure_interaction_query_service(session)


def to_interaction_resource(interaction: SecureInteraction) -> SecureInteractionResource:
    return SecureInteractionResource(
        id=interaction.id or 0,
        content_type=interaction.content_type.value,
        decision=interaction.decision.value,
        reason_code=interaction.reason_code.value,
        reason=interaction.reason,
        content_reference=interaction.content_reference,
        risk_level=interaction.risk_level,
        prompt_analysis_id=interaction.prompt_analysis_id,
        document_analysis_id=interaction.document_analysis_id,
        document_id=interaction.document_id,
        data_categories=interaction.data_categories,
        masked_findings=[
            MaskedFindingResource(
                origin=finding.origin,
                finding_type=finding.finding_type,
                severity=finding.severity,
                title=finding.title,
                location=finding.location,
                masked_evidence=finding.masked_evidence,
                occurrences=finding.occurrences,
                is_placeholder=finding.is_placeholder,
            )
            for finding in interaction.masked_findings
        ],
        generation_status=interaction.generation_status.value,
        generation_model=interaction.generation_model,
        generation_error=interaction.generation_error,
        generated_at=interaction.generated_at,
        created_at=interaction.created_at,
    )


def to_secure_query_response(result: SecureQueryResult) -> SecureQueryResponse:
    return SecureQueryResponse(
        interaction=to_interaction_resource(result.interaction),
        answer=AssistantAnswerResource(
            text=result.answer.text,
            model_name=result.answer.model_name,
            generated_at=result.answer.generated_at,
        )
        if result.answer is not None
        else None,
    )


@router.post(
    "/secure-queries",
    response_model=SecureQueryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze and ask (the main use case)",
    description=(
        "Reviews the query and an optional JSON or image attachment, applies the "
        "ALLOWED/BLOCKED policy and, "
        "only when the content was allowed and a question was submitted, asks the local model for "
        "an answer. A blocked submission never reaches the answer generator. "
        "At least a prompt or a document must be provided; when only a document is sent the response "
        "carries the review result without an answer."
    ),
    responses={
        201: {"description": "Interaction audited; the answer is present only when allowed"},
        400: {"description": "Nothing was submitted, or the document is malformed"},
        413: {"description": "The document exceeds the maximum allowed size"},
        415: {"description": "Unsupported document type"},
    },
)
async def submit_secure_query(
    command_service: Annotated[
        SubmitSecureQueryCommandServiceImpl, Depends(get_secure_query_command_service)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    prompt: Annotated[str | None, Form(description="Free-text query")] = None,
    file: Annotated[
        UploadFile | None, File(description="Optional JSON, PNG or JPEG file")
    ] = None,
) -> SecureQueryResponse:
    settings = get_settings()
    content: bytes | None = None
    if file is not None and file.filename:
        content = await file.read()
        if len(content) > settings.max_document_size_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"El documento supera el límite de {settings.max_document_size_mb} MB.",
            )
        if not content:
            content = None

    unit_of_work = SqlAlchemyUnitOfWork(session)
    try:
        command = SubmitSecureQueryCommand(
            prompt=prompt,
            document_filename=file.filename if file is not None else None,
            document_mime_type=(file.content_type or "application/octet-stream")
            if file is not None
            else None,
            document_content=content,
        )
        result = await command_service.handle_submit_secure_query(command)
        await unit_of_work.commit()
    except SecureQueryValidationError as error:
        await unit_of_work.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except ValueError as error:
        await unit_of_work.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return to_secure_query_response(result)


@router.get(
    "/interactions",
    response_model=SecureInteractionListResponse,
    summary="List audited interactions",
    description="Returns audited secure queries in reverse chronological order with bounded pagination.",
    responses={
        200: {"description": "Interaction page returned"},
        400: {"description": "Invalid pagination"},
    },
)
async def list_interactions(
    query_service: Annotated[
        SecureInteractionQueryServiceImpl, Depends(get_secure_interaction_query_service)
    ],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Interactions per page")] = 20,
) -> SecureInteractionListResponse:
    try:
        interactions, total = await query_service.handle_list_secure_interactions(
            ListSecureInteractionsQuery(page=page, page_size=page_size)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return SecureInteractionListResponse(
        items=[to_interaction_resource(interaction) for interaction in interactions],
        page=SecureInteractionPageMetadataResponse(page=page, page_size=page_size, total=total),
    )


@router.get(
    "/interactions/{interaction_id}",
    response_model=SecureInteractionResource,
    summary="Get an audited interaction",
    description="Explains why one secure query was allowed or blocked, with masked evidence only.",
    responses={
        200: {"description": "Interaction returned"},
        400: {"description": "Invalid interaction identifier"},
        404: {"description": "Interaction not found"},
    },
)
async def get_interaction(
    interaction_id: int,
    query_service: Annotated[
        SecureInteractionQueryServiceImpl, Depends(get_secure_interaction_query_service)
    ],
) -> SecureInteractionResource:
    try:
        interaction = await query_service.handle_get_secure_interaction_by_id(
            GetSecureInteractionByIdQuery(interaction_id=interaction_id)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if interaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return to_interaction_resource(interaction)
