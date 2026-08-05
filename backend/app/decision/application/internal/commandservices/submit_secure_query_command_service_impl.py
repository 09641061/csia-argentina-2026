from __future__ import annotations

import logging
from dataclasses import dataclass

from app.decision.application.internal.outboundservices.content_review_service import (
    ContentReviewService,
)
from app.decision.application.internal.outboundservices.document_intake_service import (
    DocumentIntakeService,
)
from app.decision.application.internal.outboundservices.ollama_answer_generation_client import (
    OllamaAnswerGenerationClient,
)
from app.decision.domain.exceptions import (
    AnswerGenerationContextTooLargeError,
    AnswerGenerationEmptyError,
    AnswerGenerationError,
    AnswerGenerationTimeoutError,
    AnswerGenerationUnavailableError,
)
from app.decision.domain.model.commands.submit_secure_query_command import (
    SubmitSecureQueryCommand,
)
from app.decision.domain.model.entities.secure_interaction import SecureInteraction
from app.decision.domain.model.events.secure_interaction_decided_event import (
    SecureInteractionDecidedEvent,
)
from app.decision.domain.model.valueobjects.assistant_answer import AssistantAnswer
from app.decision.domain.model.valueobjects.generation_authorization import (
    GenerationAuthorization,
)
from app.decision.domain.model.valueobjects.interaction_content_type import (
    InteractionContentType,
)
from app.decision.domain.model.valueobjects.reviewed_content_assessment import (
    ReviewedContentAssessment,
)
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.decision.domain.policies.secure_query_decision_policy import SecureQueryDecisionPolicy
from app.decision.domain.repositories.secure_interaction_repository import (
    SecureInteractionRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SecureQueryResult:
    """The outcome of one secure query: the audited interaction and, if it was allowed and asked something, the answer."""

    interaction: SecureInteraction
    answer: AssistantAnswer | None = None


class SubmitSecureQueryCommandServiceImpl:
    """
    Coordinates the three bounded contexts for "Analizar y consultar".

    Documents registers the attachment, Analysis reviews the prompt and the
    document, and this service applies the policy and only then, with a
    GenerationAuthorization in hand, calls the answer generator. The generator is
    reached from exactly one place in the codebase — the branch below — and that
    branch is unreachable unless the decision is ALLOWED and a question exists.
    """

    def __init__(
        self,
        interaction_repository: SecureInteractionRepository,
        content_review_service: ContentReviewService,
        answer_generation_client: OllamaAnswerGenerationClient,
        document_intake_service: DocumentIntakeService | None = None,
        decision_policy: SecureQueryDecisionPolicy | None = None,
    ) -> None:
        self._interaction_repository = interaction_repository
        self._content_review_service = content_review_service
        self._answer_generation_client = answer_generation_client
        self._document_intake_service = document_intake_service
        self._policy = decision_policy or SecureQueryDecisionPolicy()
        self.published_events: list[object] = []

    async def handle_submit_secure_query(
        self,
        command: SubmitSecureQueryCommand,
    ) -> SecureQueryResult:
        document_id: int | None = None
        document_reference: str | None = None

        if command.has_document:
            if self._document_intake_service is None:
                raise ValueError("Document intake is not available in this context")
            registered = await self._document_intake_service.register_document(
                filename=command.document_filename or "document.json",
                mime_type=command.document_mime_type or "application/json",
                content=command.document_content or b"",
            )
            document_id = registered.document_id
            document_reference = registered.display_name

        prompt_assessment: ReviewedContentAssessment | None = None
        document_assessment: ReviewedContentAssessment | None = None

        if command.has_prompt:
            prompt_assessment = await self._content_review_service.review_prompt(
                (command.prompt or "").strip()
            )
        if document_id is not None:
            document_assessment = await self._content_review_service.review_document(document_id)

        outcome = self._policy.evaluate(
            prompt_assessment=prompt_assessment,
            document_assessment=document_assessment,
        )

        interaction = SecureInteraction.record(
            content_type=self._content_type(command),
            decision=outcome.decision,
            reason_code=outcome.reason_code,
            reason=outcome.reason,
            content_reference=self._content_reference(
                command, document_reference, prompt_assessment, document_assessment
            ),
            risk_level=outcome.risk_level,
            prompt_analysis_id=prompt_assessment.analysis_id if prompt_assessment else None,
            document_analysis_id=document_assessment.analysis_id if document_assessment else None,
            document_id=document_id,
            masked_findings=[
                finding
                for assessment in (prompt_assessment, document_assessment)
                if assessment is not None
                for finding in assessment.findings
            ],
            data_categories=[
                category
                for assessment in (prompt_assessment, document_assessment)
                if assessment is not None
                for category in assessment.data_categories
            ],
            answer_expected=command.has_prompt,
        )

        answer: AssistantAnswer | None = None
        if outcome.decision == SecurityDecision.ALLOWED and command.has_prompt:
            authorization = GenerationAuthorization(
                decision=outcome.decision,
                prompt_analysis_id=prompt_assessment.analysis_id,  # type: ignore[union-attr]
                document_analysis_id=(
                    document_assessment.analysis_id if document_assessment else None
                ),
            )
            answer = await self._generate_answer(
                interaction=interaction,
                authorization=authorization,
                prompt=(command.prompt or "").strip(),
                document_id=document_id,
                document_reference=document_reference,
            )

        if document_id is not None and self._document_intake_service is not None:
            await self._document_intake_service.record_review_outcome(
                document_id=document_id,
                decision=outcome.decision,
                reason=outcome.reason,
            )

        saved = await self._interaction_repository.save(interaction)
        self.published_events.append(
            SecureInteractionDecidedEvent(
                interaction_id=saved.id or 0,
                decision=saved.decision,
            )
        )
        return SecureQueryResult(interaction=saved, answer=answer)

    async def _generate_answer(
        self,
        *,
        interaction: SecureInteraction,
        authorization: GenerationAuthorization,
        prompt: str,
        document_id: int | None,
        document_reference: str | None,
    ) -> AssistantAnswer | None:
        allowed_document: dict[str, object] | list[object] | None = None
        model_name = self._answer_generation_client.model_name
        try:
            if document_id is not None and self._document_intake_service is not None:
                allowed_document = await self._document_intake_service.read_allowed_document_content(
                    document_id
                )
            answer = await self._answer_generation_client.generate(
                authorization=authorization,
                prompt=prompt,
                allowed_document=allowed_document,
                document_reference=document_reference,
            )
        except AnswerGenerationError as error:
            interaction.record_failed_generation(
                authorization, model_name, self._safe_generation_error(error)
            )
            return None
        except Exception as error:  # noqa: BLE001 - a generation failure never changes the verdict
            logger.exception("Unexpected failure while generating the answer")
            interaction.record_failed_generation(
                authorization,
                model_name,
                "No fue posible generar la respuesta.",
            )
            del error
            return None

        interaction.record_successful_generation(authorization, answer.model_name)
        return answer

    def _content_type(self, command: SubmitSecureQueryCommand) -> InteractionContentType:
        if command.has_prompt and command.has_document:
            return InteractionContentType.PROMPT_WITH_DOCUMENT
        if command.has_document:
            return InteractionContentType.DOCUMENT
        return InteractionContentType.PROMPT

    def _content_reference(
        self,
        command: SubmitSecureQueryCommand,
        document_reference: str | None,
        prompt_assessment: ReviewedContentAssessment | None,
        document_assessment: ReviewedContentAssessment | None,
    ) -> str:
        if command.has_document:
            reference = document_reference or (
                document_assessment.reference if document_assessment else None
            )
            if command.has_prompt:
                return f"Consulta con {reference or 'documento adjunto'}"
            return reference or "Documento adjunto"
        if prompt_assessment is not None:
            return prompt_assessment.reference
        return "Consulta escrita"

    def _safe_generation_error(self, error: AnswerGenerationError) -> str:
        if isinstance(error, AnswerGenerationTimeoutError):
            return "El asistente local no respondió dentro del tiempo configurado."
        if isinstance(error, AnswerGenerationUnavailableError):
            return "El asistente local no está disponible en este momento."
        if isinstance(error, AnswerGenerationEmptyError):
            return "El asistente local devolvió una respuesta vacía."
        if isinstance(error, AnswerGenerationContextTooLargeError):
            return str(error)
        return "No fue posible generar la respuesta."
