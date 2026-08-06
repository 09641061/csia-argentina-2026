from datetime import datetime

from app.chat.application.internal.outboundservices.authorized_context_response_service import (
    AuthorizedContextResponseService,
)
from app.chat.domain.model.commands.send_chat_message_command import SendChatMessageCommand
from app.chat.domain.model.valueobjects.chat_message_result import ChatMessageResult
from app.decision.interfaces.acl.decision_context_facade import DecisionContextFacade


class DecisionContextResponseService(AuthorizedContextResponseService):
    def __init__(self, decision_facade: DecisionContextFacade) -> None:
        self._decision_facade = decision_facade

    async def answer(self, command: SendChatMessageCommand) -> ChatMessageResult:
        outcome = await self._decision_facade.execute_authorized_query(
            prompt=command.prompt,
            document_filename=None,
            document_mime_type=None,
            document_content=None,
        )
        generated_at = outcome["generated_at"]
        return ChatMessageResult(
            interaction_id=int(outcome["interaction_id"] or 0),
            decision=str(outcome["decision"]),
            reason=str(outcome["reason"]),
            document_id=(int(outcome["document_id"]) if outcome["document_id"] else None),
            answer=str(outcome["answer"]) if outcome["answer"] is not None else None,
            answer_model=(
                str(outcome["answer_model"])
                if outcome["answer_model"] is not None
                else None
            ),
            generated_at=generated_at if isinstance(generated_at, datetime) else None,
            attachment_url=(
                str(outcome["attachment_url"])
                if outcome.get("attachment_url") is not None
                else None
            ),
        )
