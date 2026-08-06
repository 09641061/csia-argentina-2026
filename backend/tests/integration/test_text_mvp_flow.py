import pytest
from conftest import SentinelTestContext

from app.analysis.domain.model.queries.get_analysis_by_id_query import (
    GetAnalysisByIdQuery,
)
from app.decision.domain.model.commands.submit_secure_query_command import (
    SubmitSecureQueryCommand,
)
from app.decision.domain.model.queries.get_secure_interaction_by_id_query import (
    GetSecureInteractionByIdQuery,
)
from app.decision.domain.model.queries.list_secure_interactions_query import (
    ListSecureInteractionsQuery,
)


@pytest.mark.asyncio
async def test_allowed_text_query_generates_an_answer(context: SentinelTestContext) -> None:
    result = await context.secure_query_service().handle_submit_secure_query(
        SubmitSecureQueryCommand(prompt="Explica el principio de mínimo privilegio", requested_by="alice")
    )
    await context.session.commit()

    assert result.interaction.decision.value == "allowed"
    assert result.answer is not None
    assert result.interaction.requested_by == "alice"


@pytest.mark.asyncio
async def test_blocked_text_query_never_generates_an_answer(context: SentinelTestContext) -> None:
    result = await context.secure_query_service().handle_submit_secure_query(
        SubmitSecureQueryCommand(
            prompt="La contraseña del cliente es SuperSecret123, resúmelo.",
            requested_by="alice",
        )
    )
    await context.session.commit()

    assert result.interaction.decision.value == "blocked"
    assert result.answer is None
    assert context.generation_client.calls == []


@pytest.mark.asyncio
async def test_interactions_are_isolated_by_owner(context: SentinelTestContext) -> None:
    result = await context.secure_query_service().handle_submit_secure_query(
        SubmitSecureQueryCommand(prompt="Explica autenticación multifactor", requested_by="alice")
    )
    await context.session.commit()
    interaction_id = result.interaction.id or 0
    service = context.interaction_query_service()

    visible = await service.handle_get_secure_interaction_by_id(
        GetSecureInteractionByIdQuery(interaction_id=interaction_id, requested_by="alice")
    )
    hidden = await service.handle_get_secure_interaction_by_id(
        GetSecureInteractionByIdQuery(interaction_id=interaction_id, requested_by="bob")
    )
    bob_rows, bob_total = await service.handle_list_secure_interactions(
        ListSecureInteractionsQuery(requested_by="bob")
    )

    assert visible is not None
    assert hidden is None
    assert bob_rows == []
    assert bob_total == 0


@pytest.mark.asyncio
async def test_analyses_are_isolated_by_owner(context: SentinelTestContext) -> None:
    result = await context.secure_query_service().handle_submit_secure_query(
        SubmitSecureQueryCommand(prompt="Explica cifrado simétrico", requested_by="alice")
    )
    await context.session.commit()
    analysis_id = result.interaction.prompt_analysis_id or 0
    service = context.analysis_query_service()

    visible = await service.handle_get_analysis_by_id(
        GetAnalysisByIdQuery(analysis_id=analysis_id, requested_by="alice")
    )
    hidden = await service.handle_get_analysis_by_id(
        GetAnalysisByIdQuery(analysis_id=analysis_id, requested_by="bob")
    )

    assert visible is not None
    assert hidden is None


def test_openapi_is_text_only() -> None:
    from app.main import app

    schema = app.openapi()
    assert all("document" not in path for path in schema["paths"])
    secure_query = str(schema["paths"]["/api/v1/secure-queries"]["post"]).lower()
    assert "file" not in secure_query
    assert "image" not in secure_query
