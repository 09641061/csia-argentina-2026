from typing import Protocol

from app.chat.domain.model.commands.send_chat_message_command import (
    SendChatMessageCommand,
)
from app.chat.domain.model.valueobjects.chat_message_result import ChatMessageResult


class AuthorizedContextResponseService(Protocol):
    async def answer(self, command: SendChatMessageCommand) -> ChatMessageResult: ...
