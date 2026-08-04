from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.analysis.application.internal.commandservices.document_analysis_command_service_impl import (
    DocumentAnalysisCommandServiceImpl,
)
from app.analysis.application.internal.outboundservices.document_content_downloader import DocumentContentDownloader
from app.analysis.application.internal.outboundservices.document_text_extractor import DocumentTextExtractor
from app.analysis.application.internal.outboundservices.ollama_analysis_client import OllamaAnalysisClient
from app.analysis.application.internal.outboundservices.documents.document_source_service_impl import (
    DocumentSourceServiceImpl,
)
from app.analysis.application.internal.queryservices.document_analysis_query_service_impl import (
    DocumentAnalysisQueryServiceImpl,
)
from app.analysis.domain.exceptions import (
    DocumentContentExtractionError,
    DocumentSourceNotFoundError,
)
from app.analysis.domain.model.commands.analyze_document_command import AnalyzeDocumentCommand
from app.analysis.domain.model.queries.get_document_analysis_by_document_id_query import (
    GetDocumentAnalysisByDocumentIdQuery,
)
from app.analysis.domain.model.queries.list_document_analyses_query import ListDocumentAnalysesQuery
from app.analysis.infrastructure.content.url_document_content_downloader import UrlDocumentContentDownloader
from app.analysis.infrastructure.ollama.ollama_analysis_client_impl import OllamaAnalysisClientImpl
from app.analysis.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_analysis_repository import (
    SqlAlchemyDocumentAnalysisRepository,
)
from app.analysis.infrastructure.text_extraction.json_document_text_extractor import (
    JsonDocumentTextExtractor,
)
from app.analysis.interfaces.rest.resources.analyze_document_response import AnalyzeDocumentResponse
from app.analysis.interfaces.rest.resources.analysis_finding_resource import AnalysisFindingResource
from app.analysis.interfaces.rest.resources.document_analysis_list_response import (
    DocumentAnalysisListResponse,
    DocumentAnalysisPageMetadataResponse,
)
from app.analysis.interfaces.rest.resources.document_analysis_resource import DocumentAnalysisResource
from app.core.database import get_session
from app.core.settings import get_settings
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


async def get_analysis_command_service(
    session=Depends(get_session),
) -> DocumentAnalysisCommandServiceImpl:
    settings = get_settings()
    analysis_repository = SqlAlchemyDocumentAnalysisRepository(session)
    document_repository = SqlAlchemyDocumentRepository(session)
    document_source_service = DocumentSourceServiceImpl(document_repository=document_repository)
    content_downloader = UrlDocumentContentDownloader()
    text_extractor = JsonDocumentTextExtractor()
    ollama_client = OllamaAnalysisClientImpl(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_model,
    )
    return DocumentAnalysisCommandServiceImpl(
        analysis_repository=analysis_repository,
        document_source_service=document_source_service,
        document_content_downloader=content_downloader,
        document_text_extractor=text_extractor,
        ollama_analysis_client=ollama_client,
        ollama_model_name=settings.ollama_model,
    )


async def get_analysis_query_service(session=Depends(get_session)) -> DocumentAnalysisQueryServiceImpl:
    analysis_repository = SqlAlchemyDocumentAnalysisRepository(session)
    return DocumentAnalysisQueryServiceImpl(analysis_repository=analysis_repository)


def _to_resource(analysis) -> DocumentAnalysisResource:
    return DocumentAnalysisResource(
        id=analysis.id or 0,
        document_id=analysis.document_id,
        source_filename=analysis.source_filename,
        source_mime_type=analysis.source_mime_type,
        source_document_url=analysis.source_document_url,
        risk_level=analysis.risk_level.value,
        explanation=analysis.explanation,
        model_name=analysis.model_name,
        findings=[
            AnalysisFindingResource(
                finding_type=finding.finding_type.value,
                severity=finding.severity.value,
                title=finding.title,
                description=finding.description,
                evidence=finding.evidence,
            )
            for finding in analysis.findings
        ],
        analyzed_at=analysis.analyzed_at,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.post(
    "/{document_id}",
    response_model=AnalyzeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a document",
    description="Downloads a stored document, extracts its text, runs rule-based checks and Ollama interpretation, and persists the analysis.",
    responses={
        201: {"description": "Document analyzed successfully"},
        404: {"description": "Document not found"},
        502: {"description": "Document content could not be downloaded, extracted or analyzed"},
    },
)
async def analyze_document(
    document_id: int,
    command_service: Annotated[DocumentAnalysisCommandServiceImpl, Depends(get_analysis_command_service)],
) -> AnalyzeDocumentResponse:
    try:
        command = AnalyzeDocumentCommand(document_id=document_id)
        analysis = await command_service.handle_analyze_document(command)
    except DocumentSourceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DocumentContentExtractionError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return _to_resource(analysis)


@router.get(
    "/{document_id}",
    response_model=DocumentAnalysisResource,
    status_code=status.HTTP_200_OK,
    summary="Get analysis by document ID",
    description="Retrieves the latest stored analysis for a document.",
    responses={
        200: {"description": "Analysis found"},
        404: {"description": "Analysis not found"},
    },
)
async def get_analysis_by_document_id(
    document_id: int,
    query_service: Annotated[DocumentAnalysisQueryServiceImpl, Depends(get_analysis_query_service)],
) -> DocumentAnalysisResource:
    try:
        query = GetDocumentAnalysisByDocumentIdQuery(document_id=document_id)
        analysis = await query_service.handle_get_document_analysis_by_document_id(query)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return _to_resource(analysis)


@router.get(
    "",
    response_model=DocumentAnalysisListResponse,
    status_code=status.HTTP_200_OK,
    summary="List analyses",
    description="Returns a paginated list of stored analyses.",
)
async def list_analyses(
    query_service: Annotated[DocumentAnalysisQueryServiceImpl, Depends(get_analysis_query_service)],
    page: int = 1,
    page_size: int = 20,
) -> DocumentAnalysisListResponse:
    try:
        query = ListDocumentAnalysesQuery(page=page, page_size=page_size)
        analyses, total = await query_service.handle_list_document_analyses(query)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return DocumentAnalysisListResponse(
        items=[_to_resource(analysis) for analysis in analyses],
        page=DocumentAnalysisPageMetadataResponse(page=page, page_size=page_size, total=total),
    )
