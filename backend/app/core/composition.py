"""
Composition root.

The only module allowed to know every bounded context at once. Routers ask it
for a ready-to-use application service instead of assembling collaborators
themselves, which keeps the wiring — and the security-critical order of the
steps — in one auditable place.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.application.internal.commandservices.security_analysis_command_service_impl import (
    SecurityAnalysisCommandServiceImpl,
)
from app.analysis.application.internal.outboundservices.documents.document_source_service_impl import (
    DocumentSourceServiceImpl,
)
from app.analysis.application.internal.queryservices.security_analysis_query_service_impl import (
    SecurityAnalysisQueryServiceImpl,
)
from app.analysis.infrastructure.ollama.ollama_security_analysis_client_impl import (
    OllamaSecurityAnalysisClientImpl,
)
from app.analysis.infrastructure.ollama.ollama_sensitive_content_discovery_client_impl import (
    OllamaSensitiveContentDiscoveryClientImpl,
)
from app.analysis.infrastructure.ollama.ollama_vision_extraction_client_impl import (
    OllamaVisionExtractionClientImpl,
)
from app.analysis.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_security_analysis_repository import (
    SqlAlchemySecurityAnalysisRepository,
)
from app.analysis.infrastructure.text_extraction.multi_format_document_text_extractor import (
    MultiFormatDocumentTextExtractor,
)
from app.core.settings import get_settings
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
from app.decision.infrastructure.ollama.ollama_answer_generation_client_impl import (
    OllamaAnswerGenerationClientImpl,
)
from app.decision.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_secure_interaction_repository import (
    SqlAlchemySecureInteractionRepository,
)
from app.documents.application.internal.commandservices.document_command_service_impl import (
    DocumentCommandServiceImpl,
)
from app.documents.application.internal.queryservices.document_query_service_impl import (
    DocumentQueryServiceImpl,
)
from app.documents.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)
from app.documents.infrastructure.storage.document_storage_provider import (
    get_document_storage,
)


def build_security_analysis_client() -> OllamaSecurityAnalysisClientImpl:
    settings = get_settings()
    return OllamaSecurityAnalysisClientImpl(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_security_model,
        request_timeout_seconds=settings.ollama_security_timeout_seconds,
        context_tokens=settings.ollama_security_context_tokens,
        max_output_tokens=settings.ollama_security_max_output_tokens,
    )


def build_answer_generation_client() -> OllamaAnswerGenerationClientImpl:
    settings = get_settings()
    return OllamaAnswerGenerationClientImpl(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_generation_model,
        request_timeout_seconds=settings.ollama_generation_timeout_seconds,
        context_tokens=settings.ollama_generation_context_tokens,
        max_output_tokens=settings.ollama_generation_max_output_tokens,
        max_document_characters=settings.ollama_generation_max_document_chars,
    )


def build_sensitive_content_discovery_client() -> OllamaSensitiveContentDiscoveryClientImpl:
    settings = get_settings()
    return OllamaSensitiveContentDiscoveryClientImpl(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_discovery_model,
        request_timeout_seconds=settings.ollama_discovery_timeout_seconds,
        context_tokens=settings.ollama_discovery_context_tokens,
        max_output_tokens=settings.ollama_discovery_max_output_tokens,
        max_input_characters=settings.ollama_discovery_max_input_chars,
    )


def build_vision_extraction_client() -> OllamaVisionExtractionClientImpl:
    settings = get_settings()
    return OllamaVisionExtractionClientImpl(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_vision_model,
        request_timeout_seconds=settings.ollama_vision_timeout_seconds,
        context_tokens=settings.ollama_vision_context_tokens,
        max_output_tokens=settings.ollama_vision_max_output_tokens,
    )


def build_document_text_extractor() -> MultiFormatDocumentTextExtractor:
    return MultiFormatDocumentTextExtractor(build_vision_extraction_client())


def build_document_query_service(session: AsyncSession) -> DocumentQueryServiceImpl:
    return DocumentQueryServiceImpl(
        document_repository=SqlAlchemyDocumentRepository(session),
        document_storage=get_document_storage(),
    )


def build_document_command_service(session: AsyncSession) -> DocumentCommandServiceImpl:
    settings = get_settings()
    return DocumentCommandServiceImpl(
        document_repository=SqlAlchemyDocumentRepository(session),
        document_storage=get_document_storage(),
        max_document_size_bytes=settings.max_document_size_bytes,
    )


def build_security_analysis_command_service(
    session: AsyncSession,
) -> SecurityAnalysisCommandServiceImpl:
    settings = get_settings()
    return SecurityAnalysisCommandServiceImpl(
        analysis_repository=SqlAlchemySecurityAnalysisRepository(session),
        ollama_security_analysis_client=build_security_analysis_client(),
        ollama_sensitive_content_discovery_client=(
            build_sensitive_content_discovery_client()
        ),
        security_model_name=settings.ollama_security_model,
        document_source_service=DocumentSourceServiceImpl(build_document_query_service(session)),
        document_text_extractor=build_document_text_extractor(),
        prompt_max_length=settings.prompt_max_length,
        prompt_min_length=settings.prompt_min_length,
    )


def build_security_analysis_query_service(
    session: AsyncSession,
) -> SecurityAnalysisQueryServiceImpl:
    return SecurityAnalysisQueryServiceImpl(SqlAlchemySecurityAnalysisRepository(session))


def build_secure_query_command_service(
    session: AsyncSession,
) -> SubmitSecureQueryCommandServiceImpl:
    return SubmitSecureQueryCommandServiceImpl(
        interaction_repository=SqlAlchemySecureInteractionRepository(session),
        content_review_service=ContentReviewServiceImpl(
            analysis_command_service=build_security_analysis_command_service(session),
            analysis_query_service=build_security_analysis_query_service(session),
        ),
        answer_generation_client=build_answer_generation_client(),
        document_intake_service=DocumentIntakeServiceImpl(
            document_command_service=build_document_command_service(session),
            document_query_service=build_document_query_service(session),
            document_content_extractor=build_document_text_extractor(),
        ),
    )


def build_secure_interaction_query_service(
    session: AsyncSession,
) -> SecureInteractionQueryServiceImpl:
    return SecureInteractionQueryServiceImpl(SqlAlchemySecureInteractionRepository(session))
