from typing import Protocol

from app.chat.domain.model.commands.send_chat_message_command import SendChatMessageCommand
from app.chat.domain.model.valueobjects.chat_message_result import ChatMessageResult


class ChatCommandService(Protocol):
    async def handle_send_chat_message(
        self, command: SendChatMessageCommand
    ) -> ChatMessageResult: ...
