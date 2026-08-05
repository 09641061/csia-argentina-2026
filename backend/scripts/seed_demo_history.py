"""
Populate a demo history without needing Ollama.

Runs every synthetic scenario from samples/prompt-scenarios.json through the real
Documents -> Analysis -> Decision & Audit flow, replacing only the two Ollama
clients with deterministic fakes. That makes the history screen demonstrable on
a machine where the model is not installed, while still exercising the genuine
decision logic.

    uv run python scripts/seed_demo_history.py
    uv run python scripts/seed_demo_history.py --database-url postgresql+asyncpg://postgres:admin@localhost:5432/sentinel_ai_guard
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.analysis.application.internal.commandservices.security_analysis_command_service_impl import (  # noqa: E402
    SecurityAnalysisCommandServiceImpl,
)
from app.analysis.application.internal.outboundservices.documents.document_source_service_impl import (  # noqa: E402
    DocumentSourceServiceImpl,
)
from app.analysis.application.internal.queryservices.security_analysis_query_service_impl import (  # noqa: E402
    SecurityAnalysisQueryServiceImpl,
)
from app.analysis.domain.exceptions import AnalysisModelTimeoutError  # noqa: E402
from app.analysis.domain.model.valueobjects.analysis_confidence import (  # noqa: E402
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import (  # noqa: E402
    AnalysisRiskLevel,
)
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (  # noqa: E402
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.secrets_risk_level import (  # noqa: E402
    SecretsRiskLevel,
)
from app.analysis.domain.model.valueobjects.sensitive_content_discovery import (  # noqa: E402
    SensitiveContentDiscovery,
)
from app.analysis.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_security_analysis_repository import (  # noqa: E402
    SqlAlchemySecurityAnalysisRepository,
)
from app.analysis.infrastructure.text_extraction.json_document_text_extractor import (  # noqa: E402
    JsonDocumentTextExtractor,
)
from app.decision.application.internal.commandservices.submit_secure_query_command_service_impl import (  # noqa: E402
    SubmitSecureQueryCommandServiceImpl,
)
from app.decision.application.internal.outboundservices.analysis.content_review_service_impl import (  # noqa: E402
    ContentReviewServiceImpl,
)
from app.decision.application.internal.outboundservices.documents.document_intake_service_impl import (  # noqa: E402
    DocumentIntakeServiceImpl,
)
from app.decision.domain.exceptions import AnswerGenerationTimeoutError  # noqa: E402
from app.decision.domain.model.commands.submit_secure_query_command import (  # noqa: E402
    SubmitSecureQueryCommand,
)
from app.decision.domain.model.valueobjects.assistant_answer import AssistantAnswer  # noqa: E402
from app.decision.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_secure_interaction_repository import (  # noqa: E402
    SqlAlchemySecureInteractionRepository,
)
from app.documents.application.internal.commandservices.document_command_service_impl import (  # noqa: E402
    DocumentCommandServiceImpl,
)
from app.documents.application.internal.queryservices.document_query_service_impl import (  # noqa: E402
    DocumentQueryServiceImpl,
)
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (  # noqa: E402
    SqlAlchemyDocumentRepository,
)
from app.documents.infrastructure.storage.local_document_storage import (  # noqa: E402
    LocalDocumentStorage,
)
from app.shared.infrastructure.persistence.sqlalchemy.base import Base  # noqa: E402

SAMPLES = ROOT / "samples"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{(ROOT / 'storage' / 'sentinel-demo.db').as_posix()}"

SEED_SECURITY_MODEL = "seed-security-model"
SEED_GENERATION_MODEL = "seed-generation-model"


class SeedSecurityClient:
    """Conservative fake: never lowers risk, so the deterministic rules decide."""

    def __init__(self) -> None:
        self.fail_next = False

    async def evaluate(self, *, context, findings):
        del findings
        if self.fail_next:
            raise AnalysisModelTimeoutError("Seeded analysis timeout")
        return OllamaAnalysisInterpretation(
            risk_level=AnalysisRiskLevel.LOW,
            secrets_risk=SecretsRiskLevel.NONE,
            personal_data_risk=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=False,
            data_categories=(),
            estimated_subjects=context.estimated_subjects,
            summary="Evaluacion sembrada; el resultado determinista decide.",
            rationale="El cliente sembrado no reduce el riesgo ni expone valores de origen.",
        )


class SeedDiscoveryClient:
    model_name = "seed-discovery-model"

    async def inspect(self, **kwargs):
        del kwargs
        return SensitiveContentDiscovery(
            contains_sensitive_data=False,
            risk_level=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            data_categories=(),
            model_name=self.model_name,
        )


class SeedGenerationClient:
    def __init__(self) -> None:
        self.fail_next = False

    @property
    def model_name(self) -> str:
        return SEED_GENERATION_MODEL

    async def generate(self, *, authorization, prompt, allowed_document=None, document_reference=None):
        del authorization, document_reference
        if self.fail_next:
            raise AnswerGenerationTimeoutError("Seeded generation timeout")
        suffix = " (con documento adjunto)" if allowed_document is not None else ""
        return AssistantAnswer(
            text=f"Respuesta sembrada para: {prompt[:60]}{suffix}",
            model_name=SEED_GENERATION_MODEL,
        )


def build_service(
    session: AsyncSession,
    storage: LocalDocumentStorage,
    security_client: SeedSecurityClient,
    generation_client: SeedGenerationClient,
) -> SubmitSecureQueryCommandServiceImpl:
    document_query_service = DocumentQueryServiceImpl(
        document_repository=SqlAlchemyDocumentRepository(session),
        document_storage=storage,
    )
    document_command_service = DocumentCommandServiceImpl(
        document_repository=SqlAlchemyDocumentRepository(session),
        document_storage=storage,
        max_document_size_bytes=5 * 1024 * 1024,
    )
    analysis_command_service = SecurityAnalysisCommandServiceImpl(
        analysis_repository=SqlAlchemySecurityAnalysisRepository(session),
        ollama_security_analysis_client=security_client,
        ollama_sensitive_content_discovery_client=SeedDiscoveryClient(),
        security_model_name=SEED_SECURITY_MODEL,
        document_source_service=DocumentSourceServiceImpl(document_query_service),
        document_text_extractor=JsonDocumentTextExtractor(),
    )
    return SubmitSecureQueryCommandServiceImpl(
        interaction_repository=SqlAlchemySecureInteractionRepository(session),
        content_review_service=ContentReviewServiceImpl(
            analysis_command_service=analysis_command_service,
            analysis_query_service=SecurityAnalysisQueryServiceImpl(
                SqlAlchemySecurityAnalysisRepository(session)
            ),
        ),
        answer_generation_client=generation_client,
        document_intake_service=DocumentIntakeServiceImpl(
            document_command_service=document_command_service,
            document_query_service=document_query_service,
            document_content_extractor=JsonDocumentTextExtractor(),
        ),
    )


async def seed(database_url: str) -> None:
    storage_root = ROOT / "storage" / "demo-documents"
    (ROOT / "storage").mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    scenarios = json.loads((SAMPLES / "prompt-scenarios.json").read_text(encoding="utf-8"))[
        "scenarios"
    ]

    storage = LocalDocumentStorage(root_directory=storage_root, max_content_bytes=5 * 1024 * 1024)
    security_client = SeedSecurityClient()
    generation_client = SeedGenerationClient()

    async with session_factory() as session:
        service = build_service(session, storage, security_client, generation_client)
        for scenario in scenarios:
            security_client.fail_next = scenario["simulate"] == "analysis_timeout"
            generation_client.fail_next = scenario["simulate"] == "generation_timeout"
            document_content = (
                (SAMPLES / scenario["document"]).read_bytes() if scenario["document"] else None
            )
            result = await service.handle_submit_secure_query(
                SubmitSecureQueryCommand(
                    prompt=scenario["prompt"],
                    document_filename=scenario["document"],
                    document_mime_type="application/json" if document_content else None,
                    document_content=document_content,
                )
            )
            await session.commit()
            print(
                f"{scenario['id']:<28} -> {result.interaction.decision.value:<8} "
                f"riesgo={result.interaction.risk_level or '-':<8} "
                f"generacion={result.interaction.generation_status.value}"
            )

    await engine.dispose()
    print(f"\nHistorial sembrado en {database_url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a demo history for Sentinel AI Guard")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    arguments = parser.parse_args()
    asyncio.run(seed(arguments.database_url))


if __name__ == "__main__":
    main()
