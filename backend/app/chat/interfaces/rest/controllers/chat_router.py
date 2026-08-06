from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.application.internal.conversation_application_service import (
    AssistantUnavailableError,
    ContentBlockedError,
    ConversationApplicationService,
    ConversationNotFoundError,
)
from app.chat.interfaces.rest.resources.chat_message_response import ChatMessageResponse
from app.chat.interfaces.rest.resources.conversation_resource import (
    ConversationDetailResource,
    ConversationMessageResource,
    ConversationSummaryResource,
)
from app.core.composition import (
    build_chat_command_service,
    build_conversation_title_generator,
)
from app.core.database import get_session
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.interfaces.rest.controllers.authentication_router import (
    require_authenticated_user,
)


class ChatPromptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=3, max_length=8000)


router = APIRouter(prefix="/api/v1/chat", tags=["Chat"], dependencies=[Depends(require_authenticated_user)])


def get_conversation_service(session: Annotated[AsyncSession, Depends(get_session)]) -> ConversationApplicationService:
    return ConversationApplicationService(session, build_chat_command_service(session), build_conversation_title_generator())


def _user_id(user: AuthenticatedUser) -> int:
    if user.account_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authenticated account was not found")
    return user.account_id


def _translate(error: Exception) -> None:
    if isinstance(error, ConversationNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found") from error
    if isinstance(error, ContentBlockedError):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El mensaje fue bloqueado por la política de seguridad.") from error
    if isinstance(error, AssistantUnavailableError):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "El asistente no pudo generar una respuesta.") from error


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageResponse, responses={403: {"description": "Content blocked"}, 404: {"description": "Conversation not found"}, 503: {"description": "Assistant unavailable"}})
async def send_chat_message(conversation_id: int, payload: Annotated[ChatPromptRequest, Body()], service: Annotated[ConversationApplicationService, Depends(get_conversation_service)], user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)]) -> ChatMessageResponse:
    try:
        result = await service.send_message(user_id=_user_id(user), username=user.identity, conversation_id=conversation_id, prompt=payload.prompt)
    except (ConversationNotFoundError, ContentBlockedError, AssistantUnavailableError) as error:
        _translate(error)
        raise AssertionError("unreachable")
    return ChatMessageResponse(answer=result.answer or "", conversation_id=conversation_id, model_name=result.answer_model or "", generated_at=result.generated_at)


@router.post("/conversations", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED, responses={403: {"description": "Content blocked"}, 503: {"description": "Assistant unavailable"}})
async def create_conversation(payload: Annotated[ChatPromptRequest, Body()], service: Annotated[ConversationApplicationService, Depends(get_conversation_service)], user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)]) -> ChatMessageResponse:
    try:
        conversation, result = await service.create_conversation(user_id=_user_id(user), username=user.identity, prompt=payload.prompt)
    except (ContentBlockedError, AssistantUnavailableError) as error:
        _translate(error)
        raise AssertionError("unreachable")
    return ChatMessageResponse(conversation_id=conversation.id, answer=result.answer or "", model_name=result.answer_model or "", generated_at=result.generated_at)


@router.get("/conversations", response_model=list[ConversationSummaryResource])
async def list_conversations(service: Annotated[ConversationApplicationService, Depends(get_conversation_service)], user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)], page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20) -> list[ConversationSummaryResource]:
    rows = await service.list_conversations(user_id=_user_id(user), page=page, page_size=page_size)
    return [ConversationSummaryResource.model_validate(row, from_attributes=True) for row in rows]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResource)
async def get_conversation(conversation_id: int, service: Annotated[ConversationApplicationService, Depends(get_conversation_service)], user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)], message_page: Annotated[int, Query(ge=1)] = 1, message_page_size: Annotated[int, Query(ge=1, le=100)] = 50) -> ConversationDetailResource:
    try:
        conversation, messages = await service.get_conversation(user_id=_user_id(user), conversation_id=conversation_id, page=message_page, page_size=message_page_size)
    except ConversationNotFoundError as error:
        _translate(error)
        raise AssertionError("unreachable")
    return ConversationDetailResource(id=conversation.id, title=conversation.title, created_at=conversation.created_at, updated_at=conversation.updated_at, message_page=message_page, message_page_size=message_page_size, messages=[ConversationMessageResource.model_validate(message, from_attributes=True) for message in messages])
