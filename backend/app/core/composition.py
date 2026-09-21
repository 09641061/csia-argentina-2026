"""
Composition root.

The only module allowed to know every bounded context at once. Routers ask it
for a ready-to-use application service instead of assembling collaborators
themselves, which keeps the wiring — and the security-critical order of the
steps — in one auditable place.
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.application.acl.analysis_context_facade_impl import (
    AnalysisContextFacadeImpl,
)
from app.analysis.application.internal.commandservices.security_analysis_command_service_impl import (
    SecurityAnalysisCommandServiceImpl,
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
from app.analysis.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_security_analysis_repository import (
    SqlAlchemySecurityAnalysisRepository,
)
from app.chat.application.internal.commandservices.chat_command_service_impl import (
    ChatCommandServiceImpl,
)
from app.chat.application.internal.outboundservices.acl.decision_context_response_service import (
    DecisionContextResponseService,
)
from app.chat.infrastructure.ollama.conversation_title_generator import (
    ConversationTitleGenerator,
)
from app.core.settings import get_settings
from app.decision.application.acl.decision_context_facade_impl import (
    DecisionContextFacadeImpl,
)
from app.decision.application.internal.commandservices.submit_secure_query_command_service_impl import (
    SubmitSecureQueryCommandServiceImpl,
)
from app.decision.application.internal.outboundservices.analysis.content_review_service_impl import (
    ContentReviewServiceImpl,
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


@lru_cache(maxsize=1)
def build_security_analysis_client() -> OllamaSecurityAnalysisClientImpl:
    settings = get_settings()
    return OllamaSecurityAnalysisClientImpl(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_security_model,
        request_timeout_seconds=settings.ollama_security_timeout_seconds,
        context_tokens=settings.ollama_security_context_tokens,
        max_output_tokens=settings.ollama_security_max_output_tokens,
    )


@lru_cache(maxsize=1)
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


@lru_cache(maxsize=1)
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
            AnalysisContextFacadeImpl(
                build_security_analysis_command_service(session),
                build_security_analysis_query_service(session),
            )
        ),
        answer_generation_client=build_answer_generation_client(),
    )


def build_secure_interaction_query_service(
    session: AsyncSession,
) -> SecureInteractionQueryServiceImpl:
    return SecureInteractionQueryServiceImpl(SqlAlchemySecureInteractionRepository(session))


def build_chat_command_service(session: AsyncSession) -> ChatCommandServiceImpl:
    decision_facade = DecisionContextFacadeImpl(build_secure_query_command_service(session))
    return ChatCommandServiceImpl(DecisionContextResponseService(decision_facade))


@lru_cache(maxsize=1)
def build_conversation_title_generator() -> ConversationTitleGenerator:
    settings = get_settings()
    return ConversationTitleGenerator(
        base_url=settings.ollama_base_url,
        model_name=settings.ollama_generation_model,
        timeout_seconds=settings.ollama_generation_timeout_seconds,
    )
