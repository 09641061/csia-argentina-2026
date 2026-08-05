from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.application.internal.commandservices.chat_command_service_impl import ChatCommandServiceImpl
from app.chat.domain.model.commands.send_chat_message_command import SendChatMessageCommand
from app.chat.interfaces.rest.resources.chat_message_response import ChatMessageResponse
from app.core.composition import build_chat_command_service
from app.core.database import get_session
from app.core.settings import get_settings
from app.decision.interfaces.acl.decision_context_facade import DecisionContextValidationError
from app.iam.interfaces.rest.controllers.authentication_router import require_authenticated_user
from app.shared.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

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
    "/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send an authorized chat message",
    description="Uses ACL-provided document or image context, applies security permissions and generates an answer only when authorized.",
    responses={
        201: {"description": "Message audited and processed"},
        400: {"description": "Missing message or invalid resource"},
        401: {"description": "Authentication required"},
        413: {"description": "Resource exceeds the configured size limit"},
        415: {"description": "Unsupported resource type"},
    },
)
async def send_chat_message(
    command_service: Annotated[ChatCommandServiceImpl, Depends(get_chat_command_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    prompt: Annotated[str | None, Form(description="Question for the assistant")] = None,
    file: Annotated[UploadFile | None, File(description="Optional JSON, PNG or JPEG context")] = None,
) -> ChatMessageResponse:
    content = await file.read() if file is not None and file.filename else None
    settings = get_settings()
    if content is not None and len(content) > settings.max_document_size_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Resource is too large")
    unit_of_work = SqlAlchemyUnitOfWork(session)
    try:
        result = await command_service.handle_send_chat_message(
            SendChatMessageCommand(
                prompt=prompt,
                resource_filename=file.filename if file is not None else None,
                resource_mime_type=file.content_type if file is not None else None,
                resource_content=content,
            )
        )
        await unit_of_work.commit()
    except (DecisionContextValidationError, ValueError) as error:
        await unit_of_work.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return ChatMessageResponse(
        interaction_id=result.interaction_id,
        decision=result.decision,
        reason=result.reason,
        document_id=result.document_id,
        answer=result.answer,
        answer_model=result.answer_model,
        generated_at=result.generated_at,
    )
