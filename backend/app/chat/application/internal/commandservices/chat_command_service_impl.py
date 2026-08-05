from app.chat.application.internal.outboundservices.authorized_context_response_service import (
    AuthorizedContextResponseService,
)
from app.chat.domain.model.commands.send_chat_message_command import SendChatMessageCommand
from app.chat.domain.model.valueobjects.chat_message_result import ChatMessageResult
from app.chat.domain.services.chat_command_service import ChatCommandService


class ChatCommandServiceImpl(ChatCommandService):
    def __init__(self, response_service: AuthorizedContextResponseService) -> None:
        self._response_service = response_service

    async def handle_send_chat_message(
        self, command: SendChatMessageCommand
    ) -> ChatMessageResult:
        return await self._response_service.answer(command)
