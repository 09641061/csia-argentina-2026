from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.application.internal.commandservices.document_analysis_command_service_impl import (
    DocumentAnalysisCommandServiceImpl,
)
from app.analysis.application.internal.outboundservices.documents.document_source_service_impl import (
    DocumentSourceServiceImpl,
)
from app.analysis.application.internal.queryservices.document_analysis_query_service_impl import (
    DocumentAnalysisQueryServiceImpl,
)
from app.analysis.domain.exceptions import (
    AnalysisConflictError,
    AnalysisModelInvalidResponseError,
    AnalysisModelTimeoutError,
    AnalysisModelUnavailableError,
    DocumentContentDownloadError,
    DocumentContentExtractionError,
    DocumentSourceNotFoundError,
)
from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis
from app.analysis.domain.model.queries.get_document_analysis_by_document_id_query import (
    GetDocumentAnalysisByDocumentIdQuery,
)
from app.analysis.domain.model.queries.get_document_analysis_by_id_query import (
    GetDocumentAnalysisByIdQuery,
)
from app.analysis.domain.model.queries.list_document_analyses_query import (
    ListDocumentAnalysesQuery,
)
from app.analysis.infrastructure.content.url_document_content_downloader import (
    UrlDocumentContentDownloader,
)
from app.analysis.infrastructure.ollama.ollama_analysis_client_impl import (
    OllamaAnalysisClientImpl,
)
from app.analysis.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_analysis_repository import (
    SqlAlchemyDocumentAnalysisRepository,
)
from app.analysis.infrastructure.text_extraction.json_document_text_extractor import (
    JsonDocumentTextExtractor,
)
from app.analysis.interfaces.rest.resources.analysis_finding_resource import (
    AnalysisFindingResource,
)
from app.analysis.interfaces.rest.resources.analysis_findings_response import (
    AnalysisFindingsResponse,
)
from app.analysis.interfaces.rest.resources.analyze_document_response import (
    AnalyzeDocumentResponse,
)
from app.analysis.interfaces.rest.resources.document_analysis_list_response import (
    DocumentAnalysisListResponse,
    DocumentAnalysisPageMetadataResponse,
)
from app.analysis.interfaces.rest.resources.document_analysis_resource import (
    DocumentAnalysisResource,
)
from app.analysis.interfaces.rest.resources.sanitized_document_content_response import (
    SanitizedDocumentContentResponse,
)
from app.core.database import get_session
from app.core.settings import get_settings
from app.documents.application.internal.queryservices.document_query_service_impl import (
    DocumentQueryServiceImpl,
)
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


async def get_analysis_command_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentAnalysisCommandServiceImpl:
    settings = get_settings()
    analysis_repository = SqlAlchemyDocumentAnalysisRepository(session)
    document_query_service = DocumentQueryServiceImpl(
        SqlAlchemyDocumentRepository(session)
    )
    document_source_service = DocumentSourceServiceImpl(
        document_query_service=document_query_service
    )
    return DocumentAnalysisCommandServiceImpl(
        analysis_repository=analysis_repository,
        document_source_service=document_source_service,
        document_content_downloader=UrlDocumentContentDownloader(
            settings.max_document_size_bytes
        ),
        document_text_extractor=JsonDocumentTextExtractor(),
        ollama_analysis_client=OllamaAnalysisClientImpl(
            base_url=settings.ollama_base_url,
            model_name=settings.ollama_model,
            request_timeout_seconds=settings.ollama_request_timeout_seconds,
            context_tokens=settings.ollama_context_tokens,
            max_output_tokens=settings.ollama_max_output_tokens,
        ),
        ollama_model_name=settings.ollama_model,
    )


async def get_analysis_query_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentAnalysisQueryServiceImpl:
    return DocumentAnalysisQueryServiceImpl(
        SqlAlchemyDocumentAnalysisRepository(session)
    )


def _to_finding_resource(finding: AnalysisFinding) -> AnalysisFindingResource:
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


def _to_resource(analysis: DocumentAnalysis) -> DocumentAnalysisResource:
    return DocumentAnalysisResource(
        id=analysis.id or 0,
        document_id=analysis.document_id,
        source_filename=analysis.source_filename,
        source_mime_type=analysis.source_mime_type,
        source_size_bytes=analysis.source_size_bytes,
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
        findings=[_to_finding_resource(finding) for finding in analysis.findings],
        content_truncated=analysis.content_truncated,
        has_sanitized_content=analysis.sanitized_content is not None,
        error_message=analysis.error_message,
        analyzed_at=analysis.analyzed_at,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.post(
    "/{document_id}",
    response_model=AnalyzeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a registered JSON document",
    description=(
        "Loads a document registered by Documents, scans its JSON structure, sends only a sanitized "
        "summary to local Ollama, calculates final risk, and stores a historical analysis execution."
    ),
    responses={
        201: {"description": "Analysis completed and stored"},
        400: {"description": "Invalid document identifier"},
        404: {"description": "Registered document not found"},
        409: {"description": "Another execution is already running for this document"},
        422: {"description": "Document is not analyzable JSON"},
        502: {
            "description": "Storage or Ollama returned an invalid/unavailable response"
        },
        504: {"description": "Ollama exceeded the configured timeout"},
    },
)
async def analyze_document(
    document_id: int,
    command_service: Annotated[
        DocumentAnalysisCommandServiceImpl, Depends(get_analysis_command_service)
    ],
) -> AnalyzeDocumentResponse:
    try:
        analysis = await command_service.handle_analyze_document(
            AnalyzeDocumentCommand(document_id=document_id)
        )
    except DocumentSourceNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except AnalysisConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    except DocumentContentExtractionError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except DocumentContentDownloadError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    except AnalysisModelTimeoutError as error:
        raise HTTPException(
            status.HTTP_504_GATEWAY_TIMEOUT, detail=str(error)
        ) from error
    except (AnalysisModelUnavailableError, AnalysisModelInvalidResponseError) as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while analyzing the document",
        ) from error
    return _to_resource(analysis)


@router.get(
    "/{document_id}",
    response_model=DocumentAnalysisResource,
    summary="Get latest analysis by document ID",
    description="Returns the latest historical execution for a registered document.",
    responses={
        200: {"description": "Latest execution returned"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_by_document_id(
    document_id: int,
    query_service: Annotated[
        DocumentAnalysisQueryServiceImpl, Depends(get_analysis_query_service)
    ],
) -> DocumentAnalysisResource:
    try:
        analysis = await query_service.handle_get_document_analysis_by_document_id(
            GetDocumentAnalysisByDocumentIdQuery(document_id=document_id)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _to_resource(analysis)


@router.get(
    "/runs/{analysis_id}",
    response_model=DocumentAnalysisResource,
    summary="Get an analysis execution by ID",
    description="Returns one historical analysis execution without exposing its source storage URL.",
    responses={
        200: {"description": "Execution returned"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_by_id(
    analysis_id: int,
    query_service: Annotated[
        DocumentAnalysisQueryServiceImpl, Depends(get_analysis_query_service)
    ],
) -> DocumentAnalysisResource:
    try:
        analysis = await query_service.handle_get_document_analysis_by_id(
            GetDocumentAnalysisByIdQuery(analysis_id=analysis_id)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _to_resource(analysis)


@router.get(
    "/runs/{analysis_id}/findings",
    response_model=AnalysisFindingsResponse,
    summary="Get masked findings",
    description="Returns only safe, masked findings for an analysis execution.",
    responses={
        200: {"description": "Findings returned"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_findings(
    analysis_id: int,
    query_service: Annotated[
        DocumentAnalysisQueryServiceImpl, Depends(get_analysis_query_service)
    ],
) -> AnalysisFindingsResponse:
    analysis = await query_service.handle_get_document_analysis_by_id(
        GetDocumentAnalysisByIdQuery(analysis_id=analysis_id)
    )
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return AnalysisFindingsResponse(
        analysis_id=analysis.id or 0,
        items=[_to_finding_resource(finding) for finding in analysis.findings],
    )


@router.get(
    "/runs/{analysis_id}/sanitized",
    response_model=SanitizedDocumentContentResponse,
    summary="Get sanitized JSON",
    description="Returns the independent sanitized representation; the original document is never overwritten.",
    responses={
        200: {"description": "Sanitized JSON returned"},
        404: {"description": "Analysis not found"},
        409: {"description": "This execution has no sanitized representation"},
    },
)
async def get_sanitized_content(
    analysis_id: int,
    query_service: Annotated[
        DocumentAnalysisQueryServiceImpl, Depends(get_analysis_query_service)
    ],
) -> SanitizedDocumentContentResponse:
    analysis = await query_service.handle_get_document_analysis_by_id(
        GetDocumentAnalysisByIdQuery(analysis_id=analysis_id)
    )
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    if analysis.sanitized_content is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Sanitized content is not available"
        )
    return SanitizedDocumentContentResponse(
        analysis_id=analysis.id or 0,
        document_id=analysis.document_id,
        sanitized_content=analysis.sanitized_content,
    )


@router.get(
    "",
    response_model=DocumentAnalysisListResponse,
    summary="List analysis history",
    description="Returns analysis executions in reverse creation order with bounded pagination.",
    responses={
        200: {"description": "Analysis page returned"},
        400: {"description": "Invalid pagination"},
    },
)
async def list_analyses(
    query_service: Annotated[
        DocumentAnalysisQueryServiceImpl, Depends(get_analysis_query_service)
    ],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Executions per page")
    ] = 20,
) -> DocumentAnalysisListResponse:
    try:
        analyses, total = await query_service.handle_list_document_analyses(
            ListDocumentAnalysesQuery(page=page, page_size=page_size)
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return DocumentAnalysisListResponse(
        items=[_to_resource(analysis) for analysis in analyses],
        page=DocumentAnalysisPageMetadataResponse(
            page=page, page_size=page_size, total=total
        ),
    )
