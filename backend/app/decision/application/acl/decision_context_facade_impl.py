from app.decision.application.internal.commandservices.submit_secure_query_command_service_impl import (
    SubmitSecureQueryCommandServiceImpl,
)
from app.decision.domain.model.commands.submit_secure_query_command import SubmitSecureQueryCommand
from app.decision.domain.exceptions import SecureQueryValidationError
from app.decision.interfaces.acl.decision_context_facade import (
    DecisionContextFacade,
    DecisionContextValidationError,
)


class DecisionContextFacadeImpl(DecisionContextFacade):
    """Expose the secure-query capability without leaking Decision domain objects."""

    def __init__(self, command_service: SubmitSecureQueryCommandServiceImpl) -> None:
        self._command_service = command_service

    async def execute_authorized_query(
        self,
        *,
        prompt: str | None,
        document_filename: str | None,
        document_mime_type: str | None,
        document_content: bytes | None,
    ) -> dict[str, object | None]:
        try:
            result = await self._command_service.handle_submit_secure_query(
                SubmitSecureQueryCommand(
                    prompt=prompt,
                    document_filename=document_filename,
                    document_mime_type=document_mime_type,
                    document_content=document_content,
                )
            )
        except (SecureQueryValidationError, ValueError) as error:
            raise DecisionContextValidationError(str(error)) from error
        interaction = result.interaction
        return {
            "interaction_id": interaction.id or 0,
            "decision": interaction.decision.value,
            "reason": interaction.reason,
            "document_id": interaction.document_id,
            "answer": result.answer.text if result.answer else None,
            "answer_model": result.answer.model_name if result.answer else None,
            "generated_at": result.answer.generated_at if result.answer else None,
        }
