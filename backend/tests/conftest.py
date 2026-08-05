"""
Shared test doubles and fixtures.

The automated suite never touches a real Ollama, a real Cloudinary account or
the network: every outbound collaborator has an explicit fake here, so a test
failure always points at Sentinel's own logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.analysis.application.internal.commandservices.security_analysis_command_service_impl import (
    SecurityAnalysisCommandServiceImpl,
)
from app.analysis.application.acl.analysis_context_facade_impl import AnalysisContextFacadeImpl
from app.analysis.application.internal.outboundservices.documents.document_source_service_impl import (
    DocumentSourceServiceImpl,
)
from app.analysis.application.internal.queryservices.security_analysis_query_service_impl import (
    SecurityAnalysisQueryServiceImpl,
)
from app.analysis.domain.exceptions import (
    AnalysisModelInvalidResponseError,
    AnalysisModelTimeoutError,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import AnalysisConfidence
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel
from app.analysis.domain.model.valueobjects.security_evaluation_context import (
    SecurityEvaluationContext,
)
from app.analysis.domain.model.valueobjects.sensitive_content_discovery import (
    SensitiveContentDiscovery,
)
from app.analysis.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_security_analysis_repository import (
    SqlAlchemySecurityAnalysisRepository,
)
from app.analysis.infrastructure.text_extraction.json_document_text_extractor import (
    JsonDocumentTextExtractor,
)
from app.decision.application.internal.commandservices.submit_secure_query_command_service_impl import (
    SubmitSecureQueryCommandServiceImpl,
)
from app.decision.application.internal.outboundservices.analysis.content_review_service_impl import (
    ContentReviewServiceImpl,
)
from app.decision.application.internal.outboundservices.documents.document_intake_service_impl import (
    DocumentIntakeServiceImpl,
)
from app.decision.application.internal.queryservices.secure_interaction_query_service_impl import (
    SecureInteractionQueryServiceImpl,
)
from app.decision.domain.exceptions import (
    AnswerGenerationTimeoutError,
    AnswerGenerationUnavailableError,
)
from app.decision.domain.model.valueobjects.assistant_answer import AssistantAnswer
from app.decision.domain.model.valueobjects.generation_authorization import (
    GenerationAuthorization,
)
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.decision.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_secure_interaction_repository import (
    SqlAlchemySecureInteractionRepository,
)
from app.documents.application.internal.commandservices.document_command_service_impl import (
    DocumentCommandServiceImpl,
)
from app.documents.application.acl.documents_context_facade_impl import (
    DocumentsContextFacadeImpl,
)
from app.documents.application.internal.queryservices.document_query_service_impl import (
    DocumentQueryServiceImpl,
)
from app.documents.domain.model.valueobjects.document_storage_reference import (
    DocumentStorageReference,
)
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)
from app.documents.infrastructure.storage.exceptions import DocumentStorageReadError
from app.shared.infrastructure.persistence.sqlalchemy.base import Base

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = PROJECT_ROOT / "samples"

SECURITY_MODEL = "fake-security-model"
DISCOVERY_MODEL = "fake-discovery-model"
GENERATION_MODEL = "fake-generation-model"


class InMemoryDocumentStorage:
    """Storage adapter fake: keeps bytes in memory under opaque generated keys."""

    def __init__(self) -> None:
        self.content_by_key: dict[str, bytes] = {}

    @property
    def backend_name(self) -> str:
        return "local"

    async def store(self, content: bytes, content_type: str) -> DocumentStorageReference:
        del content_type
        reference = DocumentStorageReference.for_local(f"{uuid4().hex}.json")
        self.content_by_key[reference.key] = content
        return reference

    async def read(self, reference: DocumentStorageReference) -> bytes:
        try:
            return self.content_by_key[reference.key]
        except KeyError as error:
            raise DocumentStorageReadError("The stored document is no longer available") from error


class ConservativeFakeSecurityClient:
    """
    Security model fake that never lowers risk.

    It always answers "low / none / low", which means every risk in a test comes
    from the deterministic rules. A test that ends up BLOCKED proves the
    deterministic side did the work.
    """

    def __init__(self) -> None:
        self.calls: list[SecurityEvaluationContext] = []

    async def evaluate(
        self,
        *,
        context: SecurityEvaluationContext,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation:
        del findings
        self.calls.append(context)
        return OllamaAnalysisInterpretation(
            risk_level=AnalysisRiskLevel.LOW,
            secrets_risk=SecretsRiskLevel.NONE,
            personal_data_risk=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            tampering_suspected=False,
            data_categories=(),
            estimated_subjects=context.estimated_subjects,
            summary="Fixture evaluation; the deterministic result decides.",
            rationale="The fake model provides no risk reduction and no source values.",
        )


class CleanFakeDiscoveryClient:
    model_name = DISCOVERY_MODEL

    async def inspect(self, **kwargs) -> SensitiveContentDiscovery:
        del kwargs
        return SensitiveContentDiscovery(
            contains_sensitive_data=False,
            risk_level=AnalysisRiskLevel.LOW,
            confidence=AnalysisConfidence.HIGH,
            data_categories=(),
            model_name=self.model_name,
        )


class SensitiveFakeDiscoveryClient(CleanFakeDiscoveryClient):
    async def inspect(self, **kwargs) -> SensitiveContentDiscovery:
        del kwargs
        return SensitiveContentDiscovery(
            contains_sensitive_data=True,
            risk_level=AnalysisRiskLevel.MEDIUM,
            confidence=AnalysisConfidence.HIGH,
            data_categories=("full_name", "personal_id"),
            model_name=self.model_name,
        )


class InvalidResponseFakeSecurityClient:
    async def evaluate(self, **kwargs) -> OllamaAnalysisInterpretation:
        del kwargs
        raise AnalysisModelInvalidResponseError("Invalid fake model response")


class TimeoutFakeSecurityClient:
    async def evaluate(self, **kwargs) -> OllamaAnalysisInterpretation:
        del kwargs
        raise AnalysisModelTimeoutError("Fake security model timeout")


class CrashingFakeSecurityClient:
    async def evaluate(self, **kwargs) -> OllamaAnalysisInterpretation:
        del kwargs
        raise RuntimeError("Unexpected fixture crash inside the evaluation step")


@dataclass(slots=True)
class GenerationCall:
    prompt: str
    authorization: GenerationAuthorization
    document: dict[str, object] | list[object] | None


class RecordingFakeGenerationClient:
    """Answer generator fake that records every invocation it receives."""

    def __init__(self, answer: str = "Respuesta sintética del asistente local.") -> None:
        self.calls: list[GenerationCall] = []
        self._answer = answer

    @property
    def model_name(self) -> str:
        return GENERATION_MODEL

    async def generate(
        self,
        *,
        authorization: GenerationAuthorization,
        prompt: str,
        allowed_document: dict[str, object] | list[object] | None = None,
        document_reference: str | None = None,
    ) -> AssistantAnswer:
        del document_reference
        if authorization.decision != SecurityDecision.ALLOWED:
            raise ValueError("The answer generator requires a valid ALLOWED authorization")
        self.calls.append(
            GenerationCall(prompt=prompt, authorization=authorization, document=allowed_document)
        )
        return AssistantAnswer(text=self._answer, model_name=GENERATION_MODEL)


class TimingOutFakeGenerationClient(RecordingFakeGenerationClient):
    async def generate(self, **kwargs) -> AssistantAnswer:
        self.calls.append(
            GenerationCall(
                prompt=kwargs.get("prompt", ""),
                authorization=kwargs["authorization"],
                document=kwargs.get("allowed_document"),
            )
        )
        raise AnswerGenerationTimeoutError("Fake generation timeout")


class UnavailableFakeGenerationClient(RecordingFakeGenerationClient):
    async def generate(self, **kwargs) -> AssistantAnswer:
        self.calls.append(
            GenerationCall(
                prompt=kwargs.get("prompt", ""),
                authorization=kwargs["authorization"],
                document=kwargs.get("allowed_document"),
            )
        )
        raise AnswerGenerationUnavailableError("Fake generator unavailable")


@dataclass(slots=True)
class SentinelTestContext:
    session: AsyncSession
    storage: InMemoryDocumentStorage
    security_client: object
    discovery_client: object
    generation_client: RecordingFakeGenerationClient

    def document_query_service(self) -> DocumentQueryServiceImpl:
        return DocumentQueryServiceImpl(
            document_repository=SqlAlchemyDocumentRepository(self.session),
            document_storage=self.storage,
        )

    def document_command_service(self) -> DocumentCommandServiceImpl:
        return DocumentCommandServiceImpl(
            document_repository=SqlAlchemyDocumentRepository(self.session),
            document_storage=self.storage,
            max_document_size_bytes=5 * 1024 * 1024,
        )

    def analysis_command_service(self) -> SecurityAnalysisCommandServiceImpl:
        return SecurityAnalysisCommandServiceImpl(
            analysis_repository=SqlAlchemySecurityAnalysisRepository(self.session),
            ollama_security_analysis_client=self.security_client,
            ollama_sensitive_content_discovery_client=self.discovery_client,
            security_model_name=SECURITY_MODEL,
            document_source_service=DocumentSourceServiceImpl(
                DocumentsContextFacadeImpl(
                    self.document_command_service(), self.document_query_service()
                )
            ),
            document_text_extractor=JsonDocumentTextExtractor(),
        )

    def analysis_query_service(self) -> SecurityAnalysisQueryServiceImpl:
        return SecurityAnalysisQueryServiceImpl(
            SqlAlchemySecurityAnalysisRepository(self.session)
        )

    def analysis_repository(self) -> SqlAlchemySecurityAnalysisRepository:
        return SqlAlchemySecurityAnalysisRepository(self.session)

    def interaction_query_service(self) -> SecureInteractionQueryServiceImpl:
        return SecureInteractionQueryServiceImpl(
            SqlAlchemySecureInteractionRepository(self.session)
        )

    def secure_query_service(self) -> SubmitSecureQueryCommandServiceImpl:
        return SubmitSecureQueryCommandServiceImpl(
            interaction_repository=SqlAlchemySecureInteractionRepository(self.session),
            content_review_service=ContentReviewServiceImpl(
                AnalysisContextFacadeImpl(
                    self.analysis_command_service(), self.analysis_query_service()
                )
            ),
            answer_generation_client=self.generation_client,
            document_intake_service=DocumentIntakeServiceImpl(
                documents_facade=DocumentsContextFacadeImpl(
                    self.document_command_service(), self.document_query_service()
                ),
                document_content_extractor=JsonDocumentTextExtractor(),
            ),
        )

    def sample_bytes(self, filename: str) -> bytes:
        return (SAMPLES / filename).read_bytes()


@pytest_asyncio.fixture
async def context(tmp_path: Path):
    database_path = (tmp_path / "sentinel-tests.db").as_posix()
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield SentinelTestContext(
            session=session,
            storage=InMemoryDocumentStorage(),
            security_client=ConservativeFakeSecurityClient(),
            discovery_client=CleanFakeDiscoveryClient(),
            generation_client=RecordingFakeGenerationClient(),
        )
    await engine.dispose()
