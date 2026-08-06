from app.decision.application.internal.commandservices.submit_secure_query_command_service_impl import (
    SubmitSecureQueryCommandServiceImpl,
)
from app.decision.domain.exceptions import SecureQueryValidationError
from app.decision.domain.model.commands.submit_secure_query_command import (
    SubmitSecureQueryCommand,
)
from app.decision.interfaces.acl.decision_context_facade import (
    DecisionContextFacade,
    DecisionContextValidationError,
)
from typing import Any


class DecisionContextFacadeImpl(DecisionContextFacade):
    """Expose the secure-query capability without leaking Decision domain objects."""

    def __init__(self, command_service: SubmitSecureQueryCommandServiceImpl) -> None:
        self._command_service = command_service

    async def execute_authorized_query(
        self,
        *,
        prompt: str | None,
        requested_by: str,
        attachment_payload: dict[str, Any] | list[Any] | None = None,
        attachment_name: str | None = None,
    ) -> dict[str, object | None]:
        try:
            result = await self._command_service.handle_submit_secure_query(
                SubmitSecureQueryCommand(
                    prompt=prompt,
                    requested_by=requested_by,
                    attachment_payload=attachment_payload,
                    attachment_name=attachment_name,
                )
            )
        except (SecureQueryValidationError, ValueError) as error:
            raise DecisionContextValidationError(str(error)) from error
        interaction = result.interaction
        return {
            "interaction_id": interaction.id or 0,
            "decision": interaction.decision.value,
            "reason": interaction.reason,
            "answer": result.answer.text if result.answer else None,
            "answer_model": result.answer.model_name if result.answer else None,
            "generated_at": result.answer.generated_at if result.answer else None,
        }
