from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.analysis.application.internal.commandservices.document_analysis_command_service_impl import (
    DocumentAnalysisCommandServiceImpl,
)
from app.analysis.application.internal.outboundservices.documents.document_source_service_impl import (
    DocumentSourceServiceImpl,
)
from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.document_structure_summary import (
    DocumentStructureSummary,
)
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
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
from app.documents.application.internal.queryservices.document_query_service_impl import (
    DocumentQueryServiceImpl,
)
from app.documents.domain.model.entities.document import Document
from app.documents.infrastructure.persistence.sqlalchemy.models.base import Base
from app.documents.infrastructure.persistence.sqlalchemy.models.document_model import (
    DocumentModel,
)
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = (ROOT / "samples").resolve()
DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./storage/analytics-demo.db"


class LocalSampleContentDownloader:
    async def download(self, document_url: str) -> bytes:
        path = Path(document_url).resolve()
        if not path.is_relative_to(SAMPLES_DIR) or path.suffix.lower() != ".json":
            raise ValueError(
                "Seed downloader only accepts JSON files from the samples directory"
            )
        return await asyncio.to_thread(path.read_bytes)


class DeterministicFakeOllamaClient:
    async def analyze(
        self,
        *,
        source: SourceDocumentReference,
        structure: DocumentStructureSummary,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation:
        del source
        finding_types = {finding.finding_type for finding in findings}
        real_secret_types = {
            AnalysisFindingType.PASSWORD,
            AnalysisFindingType.API_KEY,
            AnalysisFindingType.AWS_ACCESS_KEY,
            AnalysisFindingType.TOKEN,
            AnalysisFindingType.ACCESS_TOKEN,
            AnalysisFindingType.REFRESH_TOKEN,
            AnalysisFindingType.SESSION_ID,
            AnalysisFindingType.SESSION_COOKIE,
            AnalysisFindingType.CONNECTION_STRING,
        }
        if AnalysisFindingType.PRIVATE_KEY in finding_types:
            secrets_risk = SecretsRiskLevel.CRITICAL
        elif any(
            finding.finding_type in real_secret_types and not finding.is_placeholder
            for finding in findings
        ):
            secrets_risk = SecretsRiskLevel.HIGH
        elif finding_types & real_secret_types:
            secrets_risk = SecretsRiskLevel.MEDIUM
        else:
            secrets_risk = SecretsRiskLevel.NONE

        has_card_and_cvv = {
            AnalysisFindingType.CREDIT_CARD,
            AnalysisFindingType.CVV,
        }.issubset(finding_types)
        has_financial = bool(
            finding_types
            & {
                AnalysisFindingType.CREDIT_CARD,
                AnalysisFindingType.BANK_ACCOUNT,
                AnalysisFindingType.FINANCIAL_DATA,
            }
        )
        has_personal = bool(
            finding_types
            & {
                AnalysisFindingType.EMAIL,
                AnalysisFindingType.FULL_NAME,
                AnalysisFindingType.PHONE,
                AnalysisFindingType.PERSONAL_ID,
                AnalysisFindingType.PASSPORT,
            }
        )
        if has_card_and_cvv or (
            has_financial
            and structure.estimated_subjects == EstimatedSubjects.SIX_TO_ONE_HUNDRED
        ):
            personal_risk = AnalysisRiskLevel.CRITICAL
        elif has_financial or (
            has_personal
            and structure.estimated_subjects == EstimatedSubjects.SIX_TO_ONE_HUNDRED
        ):
            personal_risk = AnalysisRiskLevel.HIGH
        elif has_personal:
            personal_risk = AnalysisRiskLevel.MEDIUM
        else:
            personal_risk = AnalysisRiskLevel.LOW

        risk_order = {
            AnalysisRiskLevel.LOW: 0,
            AnalysisRiskLevel.MEDIUM: 1,
            AnalysisRiskLevel.HIGH: 2,
            AnalysisRiskLevel.CRITICAL: 3,
        }
        secret_as_risk = (
            AnalysisRiskLevel.LOW
            if secrets_risk == SecretsRiskLevel.NONE
            else AnalysisRiskLevel(secrets_risk.value)
        )
        risk_level = max(secret_as_risk, personal_risk, key=risk_order.get)
        tampering = AnalysisFindingType.PROMPT_INJECTION in finding_types
        if tampering:
            risk_level = max(risk_level, AnalysisRiskLevel.HIGH, key=risk_order.get)
        categories = tuple(
            sorted(
                {finding.data_category for finding in findings if finding.data_category}
            )
        )
        return OllamaAnalysisInterpretation(
            risk_level=risk_level,
            secrets_risk=secrets_risk,
            personal_data_risk=personal_risk,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=tampering,
            data_categories=categories,
            estimated_subjects=structure.estimated_subjects,
            summary="Review the synthetic document according to its detected risk.",
            rationale=f"Masked deterministic findings: {len(findings)}; structural volume was evaluated.",
        )


async def seed(database_url: str) -> None:
    (ROOT / "storage").mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sample_paths = sorted(
        path
        for path in SAMPLES_DIR.glob("sample-*.json")
        if path.name != "expected-results.json"
    )
    async with session_factory() as session:
        document_repository = SqlAlchemyDocumentRepository(session)
        analysis_repository = SqlAlchemyDocumentAnalysisRepository(session)
        document_query_service = DocumentQueryServiceImpl(document_repository)
        command_service = DocumentAnalysisCommandServiceImpl(
            analysis_repository=analysis_repository,
            document_source_service=DocumentSourceServiceImpl(document_query_service),
            document_content_downloader=LocalSampleContentDownloader(),
            document_text_extractor=JsonDocumentTextExtractor(),
            ollama_analysis_client=DeterministicFakeOllamaClient(),
            ollama_model_name="fake-ollama-for-seed",
        )
        created_documents = 0
        created_analyses = 0
        for sample_path in sample_paths:
            model = await session.scalar(
                select(DocumentModel)
                .where(DocumentModel.original_filename == sample_path.name)
                .limit(1)
            )
            if model is None:
                document = Document.create(
                    owner_user_id=1,
                    name=f"Synthetic analytics sample: {sample_path.stem}",
                    original_filename=sample_path.name,
                    mime_type="application/json",
                    size_bytes=sample_path.stat().st_size,
                    storage_path=str(sample_path.resolve()),
                )
                document = await document_repository.save(document)
                created_documents += 1
            else:
                document = await document_repository.find_by_id(model.id)
            if document is None or document.id is None:
                raise RuntimeError("Unable to register a synthetic sample document")
            existing = await session.scalar(
                select(DocumentAnalysisModel)
                .where(DocumentAnalysisModel.document_id == document.id)
                .limit(1)
            )
            if existing is not None:
                continue
            analysis = await command_service.handle_analyze_document(
                AnalyzeDocumentCommand(document_id=document.id)
            )
            created_analyses += 1
            print(
                f"{sample_path.name}: document_id={document.id}, analysis_id={analysis.id}, risk={analysis.risk_level.value}"
            )

    await engine.dispose()
    print(
        f"Created {created_documents} document(s) and {created_analyses} analysis execution(s)."
    )
    print(
        "Every analysis passed through extraction, detection, fake Ollama, risk calculation, and persistence."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed and analyze all synthetic Analytics datasets"
    )
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(seed(arguments.database_url))
