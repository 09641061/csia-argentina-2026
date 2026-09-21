from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.application.internal.commandservices.chat_command_service_impl import (
    ChatCommandServiceImpl,
)
from app.chat.domain.model.commands.send_chat_message_command import (
    SendChatMessageCommand,
)
from app.chat.domain.model.valueobjects.chat_message_result import ChatMessageResult
from app.chat.infrastructure.ollama.conversation_title_generator import (
    ConversationTitleGenerator,
)
from app.chat.infrastructure.persistence.sqlalchemy.models.conversation_model import (
    ConversationModel,
)
from app.chat.infrastructure.persistence.sqlalchemy.models.message_model import (
    MessageModel,
)
from app.shared.infrastructure.ollama.ollama_chat_transport import OllamaTransportError


class ConversationNotFoundError(LookupError):
    pass


class ContentBlockedError(PermissionError):
    pass


class AssistantUnavailableError(RuntimeError):
    pass


class ConversationApplicationService:
    def __init__(self, session: AsyncSession, chat_service: ChatCommandServiceImpl, title_generator: ConversationTitleGenerator) -> None:
        self._session = session
        self._chat_service = chat_service
        self._title_generator = title_generator

    async def send_message(self, *, user_id: int, username: str, conversation_id: int, prompt: str, attachment_payload=None, attachment_url: str | None = None, attachment_name: str | None = None, attachment_mime_type: str | None = None) -> ChatMessageResult:
        conversation = await self._session.scalar(select(ConversationModel).where(ConversationModel.id == conversation_id, ConversationModel.user_id == user_id))
        if conversation is None:
            raise ConversationNotFoundError
        result = await self._review_and_answer(prompt, username, attachment_payload, attachment_name)
        now = datetime.now(UTC)
        self._session.add(MessageModel(conversation_id=conversation.id, role="user", content=prompt, attachment_url=attachment_url, attachment_name=attachment_name, attachment_mime_type=attachment_mime_type, created_at=now))
        self._session.add(MessageModel(conversation_id=conversation.id, role="assistant", content=result.answer or "", secure_interaction_id=result.interaction_id, created_at=now))
        conversation.updated_at = result.generated_at or now
        await self._session.commit()
        return result

    async def create_conversation(self, *, user_id: int, username: str, prompt: str, attachment_payload=None, attachment_url: str | None = None, attachment_name: str | None = None, attachment_mime_type: str | None = None) -> tuple[ConversationModel, ChatMessageResult]:
        result = await self._review_and_answer(prompt, username, attachment_payload, attachment_name)
        now = datetime.now(UTC)
        try:
            title = await self._title_generator.generate(prompt)
        except (OllamaTransportError, ValueError):
            title = "New conversation"
        conversation = ConversationModel(user_id=user_id, title=title, created_at=now, updated_at=result.generated_at or now)
        self._session.add(conversation)
        await self._session.flush()
        self._session.add(MessageModel(conversation_id=conversation.id, role="user", content=prompt, attachment_url=attachment_url, attachment_name=attachment_name, attachment_mime_type=attachment_mime_type, created_at=now))
        self._session.add(MessageModel(conversation_id=conversation.id, role="assistant", content=result.answer or "", secure_interaction_id=result.interaction_id, created_at=now))
        await self._session.commit()
        return conversation, result

    async def list_conversations(self, *, user_id: int, page: int, page_size: int) -> list[ConversationModel]:
        return list((await self._session.scalars(select(ConversationModel).where(ConversationModel.user_id == user_id).order_by(ConversationModel.updated_at.desc()).offset((page - 1) * page_size).limit(page_size))).all())

    async def get_conversation(self, *, user_id: int, conversation_id: int, page: int, page_size: int) -> tuple[ConversationModel, list[MessageModel]]:
        conversation = await self._session.scalar(select(ConversationModel).where(ConversationModel.id == conversation_id, ConversationModel.user_id == user_id))
        if conversation is None:
            raise ConversationNotFoundError
        messages = list((await self._session.scalars(select(MessageModel).where(MessageModel.conversation_id == conversation.id).order_by(MessageModel.created_at, MessageModel.id).offset((page - 1) * page_size).limit(page_size))).all())
        return conversation, messages

    async def _review_and_answer(self, prompt: str, username: str, attachment_payload=None, attachment_name: str | None = None) -> ChatMessageResult:
        result = await self._chat_service.handle_send_chat_message(SendChatMessageCommand(prompt=prompt, requested_by=username, attachment_payload=attachment_payload, attachment_name=attachment_name))
        if result.decision == "blocked":
            await self._session.commit()
            raise ContentBlockedError
        if result.answer is None or result.answer_model is None or result.generated_at is None:
            await self._session.commit()
            raise AssistantUnavailableError
        return result
