from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.application.internal.commandservices.chat_command_service_impl import ChatCommandServiceImpl
from app.chat.domain.model.commands.send_chat_message_command import SendChatMessageCommand
from app.chat.infrastructure.ollama.conversation_title_generator import ConversationTitleGenerator
from app.chat.infrastructure.persistence.sqlalchemy.models.conversation_model import ConversationModel
from app.chat.infrastructure.persistence.sqlalchemy.models.message_model import MessageModel
from app.chat.interfaces.rest.resources.chat_message_response import ChatMessageResponse
from app.core.composition import build_chat_command_service, build_conversation_title_generator
from app.core.database import get_session
from app.decision.interfaces.acl.decision_context_facade import DecisionContextValidationError
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.infrastructure.persistence.sqlalchemy.models.user_account_model import UserAccountModel
from app.iam.interfaces.rest.controllers.authentication_router import require_authenticated_user

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


async def get_chat_command_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChatCommandServiceImpl:
    return build_chat_command_service(session)


async def _user_id(session: AsyncSession, authenticated_user: AuthenticatedUser) -> int:
    user_id = await session.scalar(
        select(UserAccountModel.id).where(
            UserAccountModel.username == authenticated_user.identity
        )
    )
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authenticated user was not found")
    return user_id


async def _answer_and_store(
    *,
    session: AsyncSession,
    command_service: ChatCommandServiceImpl,
    conversation: ConversationModel,
    prompt: str,
) -> ChatMessageResponse:
    now = datetime.now(UTC)
    session.add(
        MessageModel(
            conversation_id=conversation.id,
            role="user",
            content=prompt.strip(),
            created_at=now,
        )
    )
    try:
        result = await command_service.handle_send_chat_message(
            SendChatMessageCommand(prompt=prompt)
        )
    except (DecisionContextValidationError, ValueError) as error:
        await session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error

    if result.decision == "blocked":
        alert = f"Lo siento, no puedo procesar este mensaje. {result.reason}"
        session.add(
            MessageModel(
                conversation_id=conversation.id,
                role="assistant",
                content=alert,
                secure_interaction_id=result.interaction_id,
                created_at=now,
            )
        )
        conversation.updated_at = now
        await session.commit()
        return ChatMessageResponse(
            conversation_id=conversation.id,
            answer=alert,
            model_name="security-policy",
            generated_at=now,
        )
    if result.answer is None or result.answer_model is None or result.generated_at is None:
        await session.rollback()
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The assistant could not generate a response",
        )

    session.add(
        MessageModel(
            conversation_id=conversation.id,
            role="assistant",
            content=result.answer,
            secure_interaction_id=result.interaction_id,
            created_at=result.generated_at,
        )
    )
    conversation.updated_at = result.generated_at
    await session.commit()
    return ChatMessageResponse(
        conversation_id=conversation.id,
        answer=result.answer,
        model_name=result.answer_model,
        generated_at=result.generated_at,
    )


@router.post(
    "/conversations",
    response_model=ChatMessageResponse,
    summary="Create a conversation with its first message",
)
async def create_conversation(
    prompt: Annotated[str, Form(min_length=1, description="First message")],
    session: Annotated[AsyncSession, Depends(get_session)],
    command_service: Annotated[ChatCommandServiceImpl, Depends(get_chat_command_service)],
    title_generator: Annotated[ConversationTitleGenerator, Depends(build_conversation_title_generator)],
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> ChatMessageResponse:
    user_id = await _user_id(session, authenticated_user)
    try:
        title = await title_generator.generate(prompt)
    except Exception:
        title = "New conversation"
    now = datetime.now(UTC)
    conversation = ConversationModel(
        user_id=user_id,
        title=title,
        created_at=now,
        updated_at=now,
    )
    session.add(conversation)
    await session.flush()
    return await _answer_and_store(
        session=session,
        command_service=command_service,
        conversation=conversation,
        prompt=prompt,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    summary="Send a message to an existing conversation",
)
async def send_message(
    conversation_id: int,
    prompt: Annotated[str, Form(min_length=1, description="Message for the assistant")],
    session: Annotated[AsyncSession, Depends(get_session)],
    command_service: Annotated[ChatCommandServiceImpl, Depends(get_chat_command_service)],
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> ChatMessageResponse:
    user_id = await _user_id(session, authenticated_user)
    conversation = await session.scalar(
        select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id,
        )
    )
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return await _answer_and_store(
        session=session,
        command_service=command_service,
        conversation=conversation,
        prompt=prompt,
    )


@router.get("/conversations", summary="List the authenticated user's conversations")
async def list_conversations(
    session: Annotated[AsyncSession, Depends(get_session)],
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> list[dict[str, object]]:
    user_id = await _user_id(session, authenticated_user)
    conversations = (
        await session.scalars(
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .order_by(ConversationModel.updated_at.desc())
        )
    ).all()
    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }
        for conversation in conversations
    ]


@router.get("/conversations/{conversation_id}", summary="Get a conversation and its messages")
async def get_conversation(
    conversation_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> dict[str, object]:
    user_id = await _user_id(session, authenticated_user)
    conversation = await session.scalar(
        select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id,
        )
    )
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    messages = (
        await session.scalars(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation.id)
            .order_by(MessageModel.created_at, MessageModel.id)
        )
    ).all()
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }
