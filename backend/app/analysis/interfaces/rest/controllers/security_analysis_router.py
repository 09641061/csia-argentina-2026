from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.application.internal.commandservices.security_analysis_command_service_impl import (
    SecurityAnalysisCommandServiceImpl,
)
from app.analysis.application.internal.queryservices.security_analysis_query_service_impl import (
    SecurityAnalysisQueryServiceImpl,
)
from app.analysis.domain.exceptions import (
    AnalysisExecutionError,
    AnalysisModelInvalidResponseError,
    AnalysisModelTimeoutError,
    AnalysisModelUnavailableError,
    DocumentContentExtractionError,
    DocumentContentReadError,
    DocumentSourceNotFoundError,
    InvalidPromptError,
)
from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.commands.analyze_prompt_command import (
    AnalyzePromptCommand,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis
from app.analysis.domain.model.queries.get_analysis_by_id_query import (
    GetAnalysisByIdQuery,
)
from app.analysis.domain.model.queries.list_analyses_query import ListAnalysesQuery
from app.analysis.interfaces.rest.resources.analysis_finding_resource import (
    AnalysisFindingResource,
)
from app.analysis.interfaces.rest.resources.analysis_findings_response import (
    AnalysisFindingsResponse,
)
from app.analysis.interfaces.rest.resources.analyze_prompt_request import (
    AnalyzePromptRequest,
)
from app.analysis.interfaces.rest.resources.security_analysis_list_response import (
    SecurityAnalysisListResponse,
    SecurityAnalysisPageMetadataResponse,
)
from app.analysis.interfaces.rest.resources.security_analysis_resource import (
    SecurityAnalysisResource,
)
from app.core.composition import (
    build_security_analysis_command_service,
    build_security_analysis_query_service,
)
from app.core.database import get_session
from app.shared.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.iam.interfaces.rest.controllers.authentication_router import (
    require_authenticated_user,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Analysis"],
    dependencies=[Depends(require_authenticated_user)],
    responses={401: {"description": "Authentication required"}},
)
query_router = APIRouter(
    prefix="/api/v1",
    tags=["Analysis"],
    dependencies=[Depends(require_authenticated_user)],
    responses={401: {"description": "Authentication required"}},
)


async def get_analysis_command_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecurityAnalysisCommandServiceImpl:
    return build_security_analysis_command_service(session)


async def get_analysis_query_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecurityAnalysisQueryServiceImpl:
    return build_security_analysis_query_service(session)


def to_finding_resource(finding: AnalysisFinding) -> AnalysisFindingResource:
    return AnalysisFindingResource(
        finding_id=finding.finding_id,
        finding_type=finding.finding_type.value,
        severity=finding.severity.value,
        title=finding.title,
        description=finding.description,
        json_path=finding.json_path,
        evidence=finding.masked_evidence,
        detection_method=finding.detection_method,
        confidence=finding.confidence.value,
        occurrences=finding.occurrences,
        data_category=finding.data_category,
        is_placeholder=finding.is_placeholder,
    )


def to_analysis_resource(analysis: SecurityAnalysis) -> SecurityAnalysisResource:
    return SecurityAnalysisResource(
        id=analysis.id or 0,
        content_type=analysis.content_type.value,
        document_id=analysis.document_id,
        content_reference=analysis.content_reference,
        content_fingerprint=analysis.content_fingerprint,
        content_length=analysis.content_length,
        masked_preview=analysis.masked_preview,
        status=analysis.status.value,
        risk_level=analysis.risk_level.value if analysis.risk_level else None,
        secrets_risk=analysis.secrets_risk.value if analysis.secrets_risk else None,
        personal_data_risk=analysis.personal_data_risk.value
        if analysis.personal_data_risk
        else None,
        confidence=analysis.confidence.value if analysis.confidence else None,
        tampering_suspected=analysis.tampering_suspected,
        data_categories=analysis.data_categories,
        estimated_subjects=analysis.estimated_subjects.value,
        summary=analysis.summary,
        rationale=analysis.rationale,
        explanation=analysis.explanation,
        model_name=analysis.model_name,
        findings=[to_finding_resource(finding) for finding in analysis.findings],
        content_truncated=analysis.content_truncated,
        error_message=analysis.error_message,
        analyzed_at=analysis.analyzed_at,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


def _raise_for_analysis_error(error: Exception) -> None:
    if isinstance(error, DocumentSourceNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if isinstance(error, InvalidPromptError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if isinstance(error, DocumentContentExtractionError):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    if isinstance(error, AnalysisModelTimeoutError):
        raise HTTPException(
            status.HTTP_504_GATEWAY_TIMEOUT,
            detail="El analizador de seguridad no respondió a tiempo.",
        ) from error
    if isinstance(error, (AnalysisModelUnavailableError, AnalysisModelInvalidResponseError)):
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="El analizador de seguridad local no está disponible.",
        ) from error
    if isinstance(error, DocumentContentReadError):
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="El contenido almacenado no pudo leerse de forma segura.",
        ) from error
    if isinstance(error, AnalysisExecutionError):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La revisión de seguridad no pudo completarse.",
        ) from error


@router.post(
    "/prompts/analyses",
    response_model=SecurityAnalysisResource,
    status_code=status.HTTP_201_CREATED,
    summary="Review a free-text prompt",
    description=(
        "Runs the deterministic scan over a free-text query, masks every finding, asks the local "
        "security model for a contextual evaluation and stores a historical execution. "
        "The original prompt is never stored: only a fingerprint, a masked preview and masked findings."
    ),
    responses={
        201: {"description": "Prompt review completed and stored"},
        400: {"description": "Empty prompt or prompt outside the allowed length"},
        502: {"description": "The local security model is unavailable or returned an invalid response"},
        504: {"description": "The local security model exceeded its timeout"},
    },
)
async def analyze_prompt(
    payload: Annotated[AnalyzePromptRequest, Body()],
    command_service: Annotated[
        SecurityAnalysisCommandServiceImpl, Depends(get_analysis_command_service)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecurityAnalysisResource:
    unit_of_work = SqlAlchemyUnitOfWork(session)
    try:
        analysis = await command_service.handle_analyze_prompt(
            AnalyzePromptCommand(prompt=payload.prompt)
        )
        await unit_of_work.commit()
    except Exception as error:
        await unit_of_work.commit()
        _raise_for_analysis_error(error)
        if isinstance(error, ValueError):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La revisión de seguridad no pudo completarse.",
        ) from error
    return to_analysis_resource(analysis)


@router.post(
    "/documents/{document_id}/analyses",
    response_model=SecurityAnalysisResource,
    status_code=status.HTTP_201_CREATED,
    summary="Review a registered document",
    description=(
        "Loads a document through the controlled storage adapter, extracts a bounded structure "
        "locally (using the visual Ollama model for images and scanned pages), masks findings, "
        "requires a contextual evaluation from the security model and stores the execution."
    ),
    responses={
        201: {"description": "Document review completed and stored"},
        400: {"description": "Invalid document identifier"},
        404: {"description": "Registered document not found"},
        422: {"description": "The stored document could not be extracted safely"},
        502: {"description": "The local security model or the storage is unavailable"},
        504: {"description": "The local security model exceeded its timeout"},
    },
)
async def analyze_document(
    document_id: int,
    command_service: Annotated[
        SecurityAnalysisCommandServiceImpl, Depends(get_analysis_command_service)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecurityAnalysisResource:
    unit_of_work = SqlAlchemyUnitOfWork(session)
    try:
        analysis = await command_service.handle_analyze_document(
            AnalyzeDocumentCommand(document_id=document_id)
        )
        await unit_of_work.commit()
    except Exception as error:
        await unit_of_work.commit()
        _raise_for_analysis_error(error)
        if isinstance(error, ValueError):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La revisión de seguridad no pudo completarse.",
        ) from error
    return to_analysis_resource(analysis)


@query_router.get(
    "/analyses",
    response_model=SecurityAnalysisListResponse,
    summary="List security reviews",
    description="Returns security reviews in reverse creation order with bounded pagination.",
    responses={
        200: {"description": "Analysis page returned"},
        400: {"description": "Invalid pagination"},
    },
)
async def list_analyses(
    query_service: Annotated[SecurityAnalysisQueryServiceImpl, Depends(get_analysis_query_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Executions per page")] = 20,
) -> SecurityAnalysisListResponse:
    try:
        analyses, total = await query_service.handle_list_analyses(
            ListAnalysesQuery(page=page, page_size=page_size)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return SecurityAnalysisListResponse(
        items=[to_analysis_resource(analysis) for analysis in analyses],
        page=SecurityAnalysisPageMetadataResponse(page=page, page_size=page_size, total=total),
    )


@query_router.get(
    "/analyses/{analysis_id}",
    response_model=SecurityAnalysisResource,
    summary="Get a security review by ID",
    description="Returns one historical execution without exposing the reviewed content.",
    responses={
        200: {"description": "Execution returned"},
        400: {"description": "Invalid analysis identifier"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_by_id(
    analysis_id: int,
    query_service: Annotated[SecurityAnalysisQueryServiceImpl, Depends(get_analysis_query_service)],
) -> SecurityAnalysisResource:
    try:
        analysis = await query_service.handle_get_analysis_by_id(
            GetAnalysisByIdQuery(analysis_id=analysis_id)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return to_analysis_resource(analysis)


@query_router.get(
    "/analyses/{analysis_id}/findings",
    response_model=AnalysisFindingsResponse,
    summary="Get masked findings",
    description="Returns only safe, masked findings for one security review.",
    responses={
        200: {"description": "Findings returned"},
        400: {"description": "Invalid analysis identifier"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_findings(
    analysis_id: int,
    query_service: Annotated[SecurityAnalysisQueryServiceImpl, Depends(get_analysis_query_service)],
) -> AnalysisFindingsResponse:
    try:
        analysis = await query_service.handle_get_analysis_by_id(
            GetAnalysisByIdQuery(analysis_id=analysis_id)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return AnalysisFindingsResponse(
        analysis_id=analysis.id or 0,
        items=[to_finding_resource(finding) for finding in analysis.findings],
    )
