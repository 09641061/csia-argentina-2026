from typing import Annotated

from datetime import UTC, datetime
from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.application.internal.commandservices.chat_command_service_impl import ChatCommandServiceImpl
from app.chat.domain.model.commands.send_chat_message_command import SendChatMessageCommand
from app.chat.interfaces.rest.resources.chat_message_response import ChatMessageResponse
from app.core.composition import build_chat_command_service, build_conversation_title_generator
from app.chat.infrastructure.ollama.conversation_title_generator import ConversationTitleGenerator
from app.core.database import get_session
from app.decision.interfaces.acl.decision_context_facade import DecisionContextValidationError
from app.iam.interfaces.rest.controllers.authentication_router import require_authenticated_user
from app.shared.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.chat.infrastructure.persistence.sqlalchemy.models.conversation_model import ConversationModel
from app.chat.infrastructure.persistence.sqlalchemy.models.message_model import MessageModel
from app.iam.infrastructure.persistence.sqlalchemy.models.user_account_model import UserAccountModel
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser



router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
    dependencies=[Depends(require_authenticated_user)],
)


async def get_chat_command_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChatCommandServiceImpl:
    return build_chat_command_service(session)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the assistant",
    description="Answers a general question using optional JSON or image context. Security review, authorization and auditing remain internal.",
    responses={
        200: {"description": "Assistant answer generated"},
        400: {"description": "Missing message or invalid resource"},
        401: {"description": "Authentication required"},
        403: {"description": "The security policy blocked the submitted content"},
        413: {"description": "Resource exceeds the configured size limit"},
        415: {"description": "Unsupported resource type"},
    },
)
async def send_chat_message(
    command_service: Annotated[ChatCommandServiceImpl, Depends(get_chat_command_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    prompt: Annotated[str, Form(description="Message for the assistant")],
    conversation_id: int,
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)] = None,
    title_generator: Annotated[ConversationTitleGenerator, Depends(build_conversation_title_generator)] = None,
) -> ChatMessageResponse:
    unit_of_work = SqlAlchemyUnitOfWork(session)
    try:
        user = await session.scalar(select(UserAccountModel).where(UserAccountModel.username == authenticated_user.identity))
        now = datetime.now(UTC)
        conversation = None
        if user is not None:
            conversation = await session.scalar(select(ConversationModel).where(
                ConversationModel.id == conversation_id, ConversationModel.user_id == user.id
            ))
            if conversation is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
        if conversation is not None and prompt:
            session.add(MessageModel(conversation_id=conversation.id, role="user", content=prompt, created_at=now))
        result = await command_service.handle_send_chat_message(
            SendChatMessageCommand(
                prompt=prompt,
            )
        )
        if conversation is not None and result.answer is not None:
            session.add(MessageModel(
                conversation_id=conversation.id, role="assistant", content=result.answer,
                secure_interaction_id=result.interaction_id, created_at=result.generated_at or now,
            ))
        if conversation is not None:
            conversation.updated_at = result.generated_at or now
        await unit_of_work.commit()
    except (DecisionContextValidationError, ValueError) as error:
        await unit_of_work.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    if result.decision == "blocked":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Lo siento, tu mensaje no puede procesarse porque contiene información potencialmente peligrosa.",
        )
    if result.answer is None or result.answer_model is None or result.generated_at is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The assistant could not generate a response",
        )
    return ChatMessageResponse(
        answer=result.answer,
        conversation_id=conversation.id if conversation is not None else 0,
        model_name=result.answer_model,
        generated_at=result.generated_at,
    )


@router.post(
    "/conversations",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a conversation with its first message",
)
async def create_conversation(
    command_service: Annotated[ChatCommandServiceImpl, Depends(get_chat_command_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    prompt: Annotated[str, Form(description="First message of the conversation")],
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)] = None,
    title_generator: Annotated[ConversationTitleGenerator, Depends(build_conversation_title_generator)] = None,
) -> ChatMessageResponse:
    user = await session.scalar(select(UserAccountModel).where(UserAccountModel.username == authenticated_user.identity))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authenticated user was not found")
    now = datetime.now(UTC)
    try:
        title = await title_generator.generate(prompt)
    except Exception:
        title = "New conversation"
    conversation = ConversationModel(user_id=user.id, title=title, created_at=now, updated_at=now)
    session.add(conversation)
    await session.flush()
    session.add(MessageModel(conversation_id=conversation.id, role="user", content=prompt, created_at=now))
    try:
        result = await command_service.handle_send_chat_message(SendChatMessageCommand(prompt=prompt))
        if result.answer is not None:
            session.add(MessageModel(conversation_id=conversation.id, role="assistant", content=result.answer, secure_interaction_id=result.interaction_id, created_at=result.generated_at or now))
        conversation.updated_at = result.generated_at or now
        await session.commit()
    except (DecisionContextValidationError, ValueError) as error:
        await session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    if result.decision == "blocked":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sorry, your message cannot be processed because it contains potentially dangerous information.")
    if result.answer is None or result.answer_model is None or result.generated_at is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The assistant could not generate a response")
    return ChatMessageResponse(conversation_id=conversation.id, answer=result.answer, model_name=result.answer_model, generated_at=result.generated_at)


@router.get("/conversations", summary="List the authenticated user's conversations")
async def list_conversations(
    session: Annotated[AsyncSession, Depends(get_session)],
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> list[dict[str, object]]:
    user = await session.scalar(select(UserAccountModel).where(UserAccountModel.username == authenticated_user.identity))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authenticated user was not found")
    rows = (await session.scalars(select(ConversationModel).where(ConversationModel.user_id == user.id).order_by(ConversationModel.updated_at.desc()))).all()
    return [{"id": row.id, "title": row.title, "created_at": row.created_at, "updated_at": row.updated_at} for row in rows]


@router.get("/conversations/{conversation_id}", summary="Get a conversation with its messages")
async def get_conversation(
    conversation_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    authenticated_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> dict[str, object]:
    user = await session.scalar(select(UserAccountModel).where(UserAccountModel.username == authenticated_user.identity))
    conversation = await session.scalar(select(ConversationModel).where(
        ConversationModel.id == conversation_id, ConversationModel.user_id == user.id if user else False
    ))
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    messages = (await session.scalars(select(MessageModel).where(MessageModel.conversation_id == conversation.id).order_by(MessageModel.created_at))).all()
    return {"id": conversation.id, "title": conversation.title, "created_at": conversation.created_at,
            "updated_at": conversation.updated_at, "messages": [
                {"id": message.id, "role": message.role, "content": message.content, "created_at": message.created_at}
                for message in messages
            ]}
