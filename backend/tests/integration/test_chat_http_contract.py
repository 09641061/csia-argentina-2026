from datetime import UTC, datetime

import httpx
import pytest
from conftest import SentinelTestContext
from sqlalchemy import func, select

from app.chat.application.internal.commandservices.chat_command_service_impl import (
    ChatCommandServiceImpl,
)
from app.chat.application.internal.conversation_application_service import (
    ContentBlockedError,
    ConversationApplicationService,
)
from app.chat.application.internal.outboundservices.acl.decision_context_response_service import (
    DecisionContextResponseService,
)
from app.chat.infrastructure.persistence.sqlalchemy.models.conversation_model import (
    ConversationModel,
)
from app.chat.infrastructure.persistence.sqlalchemy.models.message_model import (
    MessageModel,
)
from app.chat.interfaces.rest.controllers import chat_router
from app.decision.application.acl.decision_context_facade_impl import (
    DecisionContextFacadeImpl,
)
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.domain.model.valueobjects.username import Username
from app.iam.interfaces.rest.controllers.authentication_router import (
    require_authenticated_user,
)
from app.main import app


class FakeTitleGenerator:
    async def generate(self, prompt: str) -> str:
        return prompt[:40]


@pytest.mark.asyncio
async def test_blocked_chat_does_not_persist_conversation_or_message(context: SentinelTestContext) -> None:
    chat_service = ChatCommandServiceImpl(DecisionContextResponseService(DecisionContextFacadeImpl(context.secure_query_service())))
    service = ConversationApplicationService(context.session, chat_service, FakeTitleGenerator())

    with pytest.raises(ContentBlockedError):
        await service.create_conversation(user_id=1, username="alice", prompt="La contraseña es SuperSecret123")

    assert await context.session.scalar(select(func.count(ConversationModel.id))) == 0
    assert await context.session.scalar(select(func.count(MessageModel.id))) == 0


class FakeConversationService:
    async def create_conversation(self, **kwargs):
        del kwargs
        class Conversation:
            id = 7
        class Result:
            answer = "respuesta"
            answer_model = "fake"
            generated_at = datetime.now(UTC)
        return Conversation(), Result()


@pytest.mark.asyncio
async def test_create_conversation_http_contract_is_json_and_201() -> None:
    app.dependency_overrides[require_authenticated_user] = lambda: AuthenticatedUser(Username("alice"), account_id=1)
    app.dependency_overrides[chat_router.get_conversation_service] = lambda: FakeConversationService()
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/chat/conversations", json={"prompt": "Explica DDD"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["conversation_id"] == 7
