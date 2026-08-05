"""HTTP-level guarantees: route shape, safe payloads and pagination."""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select

from app.analysis.interfaces.rest.controllers import security_analysis_router
from app.chat.application.internal.commandservices.chat_command_service_impl import (
    ChatCommandServiceImpl,
)
from app.chat.application.internal.outboundservices.acl.decision_context_response_service import (
    DecisionContextResponseService,
)
from app.chat.interfaces.rest.controllers import chat_router
from app.core.database import get_session
from app.decision.application.acl.decision_context_facade_impl import (
    DecisionContextFacadeImpl,
)
from app.decision.interfaces.rest.controllers import secure_query_router
from app.documents.interfaces.rest.controllers import document_router
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.domain.model.valueobjects.username import Username
from app.iam.infrastructure.persistence.sqlalchemy.models.user_account_model import (
    UserAccountModel,
)
from app.iam.interfaces.rest.controllers import authentication_router
from app.main import create_app
from tests.conftest import SentinelTestContext


def build_test_app(context: SentinelTestContext) -> FastAPI:
    app = FastAPI()
    app.include_router(document_router.router)
    app.include_router(security_analysis_router.router)
    app.include_router(secure_query_router.router)
    app.include_router(chat_router.router)

    async def session_override():
        yield context.session

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[document_router.get_document_command_service] = (
        context.document_command_service
    )
    app.dependency_overrides[document_router.get_document_query_service] = (
        context.document_query_service
    )
    app.dependency_overrides[security_analysis_router.get_analysis_command_service] = (
        context.analysis_command_service
    )
    app.dependency_overrides[security_analysis_router.get_analysis_query_service] = (
        context.analysis_query_service
    )
    app.dependency_overrides[secure_query_router.get_secure_query_command_service] = (
        context.secure_query_service
    )
    app.dependency_overrides[
        secure_query_router.get_secure_interaction_query_service
    ] = context.interaction_query_service
    app.dependency_overrides[chat_router.get_chat_command_service] = lambda: (
        ChatCommandServiceImpl(
            DecisionContextResponseService(
                DecisionContextFacadeImpl(context.secure_query_service())
            )
        )
    )

    async def authenticated_user_override():
        return AuthenticatedUser(username=Username("admin"))

    app.dependency_overrides[authentication_router.require_authenticated_user] = (
        authenticated_user_override
    )
    return app


def client_for(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    )


def test_routes_are_unambiguous_and_documented() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]

    assert set(paths) == {
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/me",
        "/api/v1/chat/messages",
        "/api/v1/documents",
        "/api/v1/documents/{document_id}",
        "/api/v1/documents/{document_id}/table",
        "/api/v1/documents/{document_id}/analyses",
        "/api/v1/prompts/analyses",
        "/api/v1/analyses",
        "/api/v1/analyses/{analysis_id}",
        "/api/v1/analyses/{analysis_id}/findings",
        "/api/v1/secure-queries",
        "/api/v1/interactions",
        "/api/v1/interactions/{interaction_id}",
        "/api/v1/platform/overview",
        "/api/v1/platform/policies/current",
        "/api/v1/platform/sanitize",
        "/api/v1/platform/interactions/{interaction_id}/trace",
        "/api/v1/platform/approvals",
        "/api/v1/platform/approvals/{approval_id}/resolve",
        "/api/v1/platform/lab/scenarios",
        "/api/v1/platform/reports/{interaction_id}.pdf",
    }
    # A static segment and a path parameter must never compete for the same slot.
    assert "/api/v1/analyses/runs" not in paths
    for operations in paths.values():
        for operation in operations.values():
            assert operation.get("summary")
            assert operation.get("description")


def test_public_schema_never_declares_internal_storage_fields() -> None:
    schema = create_app().openapi()
    serialized = json.dumps(schema)

    for forbidden in (
        "storage_path",
        "storage_reference",
        "source_document_url",
        "sanitized_content",
        "cloudinary",
        "CLOUDINARY_API_SECRET",
        "database_url",
    ):
        assert forbidden not in serialized


@pytest.mark.asyncio
async def test_real_document_query_dependency_includes_readable_storage(
    context: SentinelTestContext,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        document_router, "get_document_storage", lambda: context.storage
    )

    service = await document_router.get_document_query_service(context.session)

    assert service._document_storage is context.storage


@pytest.mark.asyncio
async def test_iam_registration_login_and_jwt_validation(
    context: SentinelTestContext,
) -> None:
    app = FastAPI()
    app.include_router(authentication_router.router)

    async def session_override():
        yield context.session

    app.dependency_overrides[get_session] = session_override
    async with client_for(app) as client:
        registered = await client.post(
            "/api/v1/auth/register",
            json={"username": "sentinel.demo", "password": "DemoSecure2026"},
        )
        duplicate = await client.post(
            "/api/v1/auth/register",
            json={"username": "SENTINEL.DEMO", "password": "DemoSecure2026"},
        )
        accepted = await client.post(
            "/api/v1/auth/login",
            json={"username": "sentinel.demo", "password": "DemoSecure2026"},
        )
        rejected = await client.post(
            "/api/v1/auth/login",
            json={"username": "sentinel.demo", "password": "WrongPass2026"},
        )
        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {accepted.json()['access_token']}"},
        )
    stored_account = (
        await context.session.execute(
            select(UserAccountModel).where(UserAccountModel.username == "sentinel.demo")
        )
    ).scalar_one()

    assert registered.status_code == 201
    assert duplicate.status_code == 409
    assert accepted.status_code == 200
    assert accepted.json()["token_type"] == "bearer"
    assert accepted.json()["access_token"]
    assert accepted.json()["username"] == "sentinel.demo"
    assert rejected.status_code == 401
    assert me.status_code == 200
    assert me.json() == {"username": "sentinel.demo"}
    assert stored_account.password_hash.startswith("$argon2")
    assert "DemoSecure2026" not in stored_account.password_hash


@pytest.mark.asyncio
async def test_protected_routes_require_a_bearer_token() -> None:
    app = FastAPI()
    app.include_router(document_router.router)
    async with client_for(app) as client:
        response = await client.get("/api/v1/documents")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_secure_query_endpoint_returns_answer_only_when_allowed(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)
    async with client_for(app) as client:
        allowed = await client.post(
            "/api/v1/secure-queries",
            data={"prompt": "Explícame qué es una arquitectura orientada a eventos."},
        )
        blocked = await client.post(
            "/api/v1/secure-queries",
            data={"prompt": "La contraseña del cliente es SuperSecret123, resúmelo."},
        )

    assert allowed.status_code == 201
    assert allowed.json()["interaction"]["decision"] == "allowed"
    assert allowed.json()["answer"]["text"]

    assert blocked.status_code == 201
    body = blocked.json()
    assert body["interaction"]["decision"] == "blocked"
    assert body["answer"] is None
    assert body["interaction"]["generation_status"] == "skipped"
    assert "SuperSecret123" not in blocked.text


@pytest.mark.asyncio
async def test_secure_query_endpoint_requires_content(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)
    async with client_for(app) as client:
        response = await client.post("/api/v1/secure-queries", data={})

    assert response.status_code == 400
    assert "al menos una consulta" in response.json()["detail"]


@pytest.mark.asyncio
async def test_document_upload_and_analysis_over_http(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)
    payload = context.sample_bytes("sample-01-clean-inventory.json")

    async with client_for(app) as client:
        upload = await client.post(
            "/api/v1/documents",
            files={"file": ("inventario.json", payload, "application/json")},
        )
        document_id = upload.json()["id"]
        analysis = await client.post(f"/api/v1/documents/{document_id}/analyses")
        analysis_id = analysis.json()["id"]
        findings = await client.get(f"/api/v1/analyses/{analysis_id}/findings")
        listing = await client.get("/api/v1/analyses?page=1&page_size=5")
        detail = await client.get(f"/api/v1/analyses/{analysis_id}")
        documents = await client.get("/api/v1/documents")
        table = await client.get(f"/api/v1/documents/{document_id}/table")

    assert upload.status_code == 201
    assert "storage_reference" not in upload.text
    assert analysis.status_code == 201
    assert analysis.json()["risk_level"] == "low"
    assert findings.status_code == 200
    assert listing.status_code == 200
    assert detail.status_code == 200
    assert documents.status_code == 200
    assert documents.json()["page"]["total"] == 1
    assert table.status_code == 200
    assert table.json()["total_rows"] == 10
    assert "name" in table.json()["columns"]
    assert table.json()["metadata"]["report"] == "Service inventory"


@pytest.mark.asyncio
async def test_chat_uses_the_acl_backed_secure_query_flow(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)
    async with client_for(app) as client:
        response = await client.post(
            "/api/v1/chat/messages",
            data={"prompt": "Explica qué es una arquitectura orientada a eventos."},
        )

    assert response.status_code == 200
    assert response.json()["answer"]
    assert set(response.json()) == {"answer", "model_name", "generated_at"}


@pytest.mark.asyncio
async def test_chat_hides_auditing_details_and_returns_forbidden_when_blocked(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)
    async with client_for(app) as client:
        response = await client.post(
            "/api/v1/chat/messages",
            data={"prompt": "La contraseña del cliente es SuperSecret123, resúmelo."},
        )

    assert response.status_code == 403
    assert "SuperSecret123" not in response.text
    assert "interaction_id" not in response.text
    assert "decision" not in response.text


@pytest.mark.asyncio
async def test_rejected_uploads_return_safe_status_codes(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)

    async with client_for(app) as client:
        broken = await client.post(
            "/api/v1/documents",
            files={"file": ("broken.json", b"{not json", "application/json")},
        )
        unsupported_pdf = await client.post(
            "/api/v1/documents",
            files={"file": ("report.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert broken.status_code == 400
    assert unsupported_pdf.status_code == 415
    assert "Traceback" not in broken.text
    assert "app/" not in unsupported_pdf.text


@pytest.mark.asyncio
async def test_interaction_history_pagination_and_detail(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)

    async with client_for(app) as client:
        for index in range(3):
            await client.post(
                "/api/v1/secure-queries",
                data={"prompt": f"Explica el patrón repositorio, versión {index}."},
            )
        first_page = await client.get("/api/v1/interactions?page=1&page_size=2")
        second_page = await client.get("/api/v1/interactions?page=2&page_size=2")
        detail_id = first_page.json()["items"][0]["id"]
        detail = await client.get(f"/api/v1/interactions/{detail_id}")
        missing = await client.get("/api/v1/interactions/999999")
        invalid_page = await client.get("/api/v1/interactions?page=0")

    assert first_page.json()["page"]["total"] == 3
    assert len(first_page.json()["items"]) == 2
    assert len(second_page.json()["items"]) == 1
    assert detail.status_code == 200
    assert detail.json()["id"] == detail_id
    assert missing.status_code == 404
    assert invalid_page.status_code == 422


@pytest.mark.asyncio
async def test_prompt_analysis_endpoint_rejects_empty_and_oversized_prompts(
    context: SentinelTestContext,
) -> None:
    app = build_test_app(context)

    async with client_for(app) as client:
        empty = await client.post("/api/v1/prompts/analyses", json={"prompt": "   "})
        oversized = await client.post(
            "/api/v1/prompts/analyses", json={"prompt": "a" * 9000}
        )
        valid = await client.post(
            "/api/v1/prompts/analyses",
            json={"prompt": "¿Cuáles son las ventajas de la arquitectura hexagonal?"},
        )

    assert empty.status_code == 400
    assert oversized.status_code == 422
    assert valid.status_code == 201
    assert valid.json()["content_type"] == "prompt"
    assert valid.json()["risk_level"] == "low"


def test_cors_is_restricted_to_the_configured_frontend_origin() -> None:
    app = create_app()
    cors = [
        middleware for middleware in app.user_middleware if "CORS" in str(middleware)
    ]

    assert cors, "CORS middleware must be configured"
    origins = cors[0].kwargs["allow_origins"]
    assert "*" not in origins
    assert any(origin.endswith(":5173") for origin in origins)
