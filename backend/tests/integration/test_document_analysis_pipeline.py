from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.analysis.application.internal.commandservices.document_analysis_command_service_impl import (
    DocumentAnalysisCommandServiceImpl,
)
from app.analysis.application.internal.outboundservices.documents.document_source_service_impl import (
    DocumentSourceServiceImpl,
)
from app.analysis.application.internal.queryservices.document_analysis_query_service_impl import (
    DocumentAnalysisQueryServiceImpl,
)
from app.analysis.domain.exceptions import AnalysisModelInvalidResponseError
from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.analysis_status import AnalysisStatus
from app.analysis.domain.model.valueobjects.document_structure_summary import (
    DocumentStructureSummary,
)
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel
from app.analysis.domain.model.valueobjects.source_document_reference import (
    SourceDocumentReference,
)
from app.analysis.infrastructure.persistence.sqlalchemy.models.document_analysis_model import (
    DocumentAnalysisModel,
)
from app.analysis.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_analysis_repository import (
    SqlAlchemyDocumentAnalysisRepository,
)
from app.analysis.infrastructure.text_extraction.json_document_text_extractor import (
    JsonDocumentTextExtractor,
)
from app.analysis.interfaces.rest.controllers.document_analysis_router import (
    get_analysis_command_service,
    get_analysis_query_service,
    router,
)
from app.documents.application.internal.queryservices.document_query_service_impl import (
    DocumentQueryServiceImpl,
)
from app.documents.domain.model.entities.document import Document
from app.documents.infrastructure.persistence.sqlalchemy.models.base import Base
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "samples"


class MemoryContentDownloader:
    def __init__(self) -> None:
        self.content_by_reference: dict[str, bytes] = {}

    async def download(self, document_url: str) -> bytes:
        return self.content_by_reference[document_url]


class ConservativeFakeOllamaClient:
    async def analyze(
        self,
        *,
        source: SourceDocumentReference,
        structure: DocumentStructureSummary,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation:
        del source, findings
        return OllamaAnalysisInterpretation(
            risk_level=AnalysisRiskLevel.LOW,
            secrets_risk=SecretsRiskLevel.NONE,
            personal_data_risk=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=False,
            data_categories=(),
            estimated_subjects=structure.estimated_subjects,
            summary="Use the deterministic result for this synthetic fixture.",
            rationale="The fake model intentionally provides no risk reduction or source values.",
        )


class InvalidFakeOllamaClient:
    async def analyze(self, **kwargs):
        del kwargs
        raise AnalysisModelInvalidResponseError("Invalid fake model response")


@dataclass(slots=True)
class IntegrationContext:
    engine: AsyncEngine
    session: AsyncSession
    document_repository: SqlAlchemyDocumentRepository
    analysis_repository: SqlAlchemyDocumentAnalysisRepository
    downloader: MemoryContentDownloader

    def command_service(self, ollama_client=None) -> DocumentAnalysisCommandServiceImpl:
        document_query_service = DocumentQueryServiceImpl(self.document_repository)
        return DocumentAnalysisCommandServiceImpl(
            analysis_repository=self.analysis_repository,
            document_source_service=DocumentSourceServiceImpl(document_query_service),
            document_content_downloader=self.downloader,
            document_text_extractor=JsonDocumentTextExtractor(),
            ollama_analysis_client=ollama_client or ConservativeFakeOllamaClient(),
            ollama_model_name="fake-ollama-test",
        )

    async def register_sample(self, filename: str) -> Document:
        sample_path = SAMPLES / filename
        reference = f"memory://{filename}"
        self.downloader.content_by_reference[reference] = sample_path.read_bytes()
        return await self.document_repository.save(
            Document.create(
                owner_user_id=1,
                name=f"Integration fixture {filename}",
                original_filename=filename,
                mime_type="application/json",
                size_bytes=sample_path.stat().st_size,
                storage_path=reference,
            )
        )


@pytest_asyncio.fixture
async def context(tmp_path: Path):
    database_path = (tmp_path / "analytics-tests.db").as_posix()
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield IntegrationContext(
            engine=engine,
            session=session,
            document_repository=SqlAlchemyDocumentRepository(session),
            analysis_repository=SqlAlchemyDocumentAnalysisRepository(session),
            downloader=MemoryContentDownloader(),
        )
    await engine.dispose()


@pytest.mark.asyncio
async def test_all_datasets_run_through_pipeline_and_history(
    context: IntegrationContext,
) -> None:
    manifest = json.loads(
        (SAMPLES / "expected-results.json").read_text(encoding="utf-8")
    )
    service = context.command_service()
    analyses = []
    documents = []

    for expected in manifest["datasets"]:
        document = await context.register_sample(expected["file"])
        analysis = await service.handle_analyze_document(
            AnalyzeDocumentCommand(document.id)
        )
        documents.append(document)
        analyses.append(analysis)
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.risk_level.value in expected["expected_risk"]
        assert len(analysis.findings) >= expected["minimum_findings"]
        assert set(expected["expected_finding_types"]).issubset(
            {finding.finding_type.value for finding in analysis.findings}
        )
        assert set(expected["expected_categories"]).issubset(
            set(analysis.data_categories)
        )
        assert analysis.tampering_suspected is expected["tampering_expected"]

    page, total = await context.analysis_repository.list(page=1, page_size=4)
    assert total == 10
    assert len(page) == 4

    end_analysis = analyses[-1]
    assert any(
        finding.json_path.startswith("$.records[349]")
        for finding in end_analysis.findings
    )
    assert end_analysis.content_truncated is True

    second_run = await service.handle_analyze_document(
        AnalyzeDocumentCommand(documents[0].id)
    )
    latest = await context.analysis_repository.find_by_document_id(documents[0].id)
    _, total_after_reanalysis = await context.analysis_repository.list(
        page=1, page_size=100
    )
    assert latest.id == second_run.id
    assert second_run.id != analyses[0].id
    assert total_after_reanalysis == 11


@pytest.mark.asyncio
async def test_persistence_and_http_responses_never_contain_complete_secrets(
    context: IntegrationContext,
) -> None:
    document = await context.register_sample("sample-03-credentials-dump.json")
    service = context.command_service()

    app = FastAPI()
    app.include_router(router)
    query_service = DocumentAnalysisQueryServiceImpl(context.analysis_repository)
    app.dependency_overrides[get_analysis_command_service] = lambda: service
    app.dependency_overrides[get_analysis_query_service] = lambda: query_service
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/v1/analysis/{document.id}")
        assert response.status_code == 201
        body = response.text
        analysis_id = response.json()["id"]
        assert "source_document_url" not in response.json()

        findings_response = await client.get(
            f"/api/v1/analysis/runs/{analysis_id}/findings"
        )
        sanitized_response = await client.get(
            f"/api/v1/analysis/runs/{analysis_id}/sanitized"
        )
        list_response = await client.get("/api/v1/analysis?page=1&page_size=5")
        assert findings_response.status_code == 200
        assert sanitized_response.status_code == 200
        assert list_response.status_code == 200
        body += findings_response.text + sanitized_response.text + list_response.text

    model = await context.session.scalar(
        select(DocumentAnalysisModel).where(DocumentAnalysisModel.id == analysis_id)
    )
    assert model is not None
    persisted = json.dumps(
        {
            "findings": model.findings,
            "sanitized_content": model.sanitized_content,
            "summary": model.summary,
            "rationale": model.rationale,
        }
    )
    complete_values = (
        "S3nt1nel-Pr0d-2026!",
        "sk-proj4Xm2QpLd8Rt6VbNc1Zk9WsYh3Ge7Uf5Ja",
        "AKIA4XM2QPLD8RT6VBNC",
        "ghp_7f2c1b8d9a4e5f6c7d8e",
        "DemoService-00-Pass!",
    )
    for complete_value in complete_values:
        assert complete_value not in persisted
        assert complete_value not in body


@pytest.mark.asyncio
async def test_invalid_ollama_response_persists_failed_execution_without_low_risk(
    context: IntegrationContext,
) -> None:
    document = await context.register_sample("sample-01-clean-inventory.json")
    service = context.command_service(InvalidFakeOllamaClient())

    with pytest.raises(AnalysisModelInvalidResponseError):
        await service.handle_analyze_document(AnalyzeDocumentCommand(document.id))

    failed = await context.analysis_repository.find_by_document_id(document.id)
    assert failed is not None
    assert failed.status == AnalysisStatus.FAILED
    assert failed.risk_level is None
    assert failed.secrets_risk is None
    assert failed.personal_data_risk is None
    assert (
        failed.error_message
        == "Ollama analysis did not complete with a valid response."
    )
