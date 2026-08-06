from __future__ import annotations

import logging
import json

from app.decision.application.internal.outboundservices.content_review_service import (
    ContentReviewService,
)
from app.decision.application.internal.outboundservices.ollama_answer_generation_client import (
    OllamaAnswerGenerationClient,
)
from app.decision.domain.exceptions import (
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
from app.decision.domain.model.valueobjects.secure_query_result import SecureQueryResult
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.decision.domain.policies.secure_query_decision_policy import (
    SecureQueryDecisionPolicy,
)
from app.decision.domain.repositories.secure_interaction_repository import (
    SecureInteractionRepository,
)
from app.decision.domain.services.secure_query_command_service import (
    SecureQueryCommandService,
)

logger = logging.getLogger(__name__)


class SubmitSecureQueryCommandServiceImpl(SecureQueryCommandService):
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
        decision_policy: SecureQueryDecisionPolicy | None = None,
    ) -> None:
        self._interaction_repository = interaction_repository
        self._content_review_service = content_review_service
        self._answer_generation_client = answer_generation_client
        self._policy = decision_policy or SecureQueryDecisionPolicy()
        self.published_events: list[object] = []

    async def handle_submit_secure_query(
        self,
        command: SubmitSecureQueryCommand,
    ) -> SecureQueryResult:
        prompt_assessment = await self._content_review_service.review_prompt(
            (command.prompt or "").strip(), command.requested_by
        )

        document_assessment = None
        if command.attachment_payload is not None:
            # Review the exact locally extracted representation that will later
            # be supplied to the answer model; the original bytes never bypass
            # the security boundary.
            document_assessment = await self._content_review_service.review_prompt(
                json.dumps(command.attachment_payload, ensure_ascii=False),
                command.requested_by,
            )

        outcome = self._policy.evaluate(
            prompt_assessment=prompt_assessment,
            document_assessment=document_assessment,
        )

        interaction = SecureInteraction.record(
            content_type=(InteractionContentType.PROMPT_WITH_DOCUMENT if document_assessment else InteractionContentType.PROMPT),
            decision=outcome.decision,
            reason_code=outcome.reason_code,
            reason=outcome.reason,
            content_reference=prompt_assessment.reference,
            risk_level=outcome.risk_level,
            prompt_analysis_id=prompt_assessment.analysis_id if prompt_assessment else None,
            document_analysis_id=document_assessment.analysis_id if document_assessment else None,
            document_id=None,
            masked_findings=list(prompt_assessment.findings) + (list(document_assessment.findings) if document_assessment else []),
            data_categories=list(prompt_assessment.data_categories) + (list(document_assessment.data_categories) if document_assessment else []),
            answer_expected=True,
            requested_by=command.requested_by,
        )

        answer: AssistantAnswer | None = None
        if outcome.decision == SecurityDecision.ALLOWED:
            authorization = GenerationAuthorization(
                decision=outcome.decision,
                prompt_analysis_id=prompt_assessment.analysis_id,  # type: ignore[union-attr]
                document_analysis_id=document_assessment.analysis_id if document_assessment else None,
            )
            answer = await self._generate_answer(
                interaction=interaction,
                authorization=authorization,
                prompt=(command.prompt or "").strip(),
                allowed_document=command.attachment_payload,
                document_reference=command.attachment_name,
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
        allowed_document: dict[str, object] | list[object] | None = None,
        document_reference: str | None = None,
    ) -> AssistantAnswer | None:
        model_name = self._answer_generation_client.model_name
        try:
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
        except Exception as error:
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

    def _safe_generation_error(self, error: AnswerGenerationError) -> str:
        if isinstance(error, AnswerGenerationTimeoutError):
            return "El asistente local no respondió dentro del tiempo configurado."
        if isinstance(error, AnswerGenerationUnavailableError):
            return "El asistente local no está disponible en este momento."
        if isinstance(error, AnswerGenerationEmptyError):
            return "El asistente local devolvió una respuesta vacía."
        return "No fue posible generar la respuesta."
