"""
Every synthetic scenario in samples/prompt-scenarios.json is executed for real.

The manifest is the shared contract between the test suite, the seed script and
the demo: if a scenario stops behaving as declared, this test fails.
"""

from __future__ import annotations

import json

import pytest

from app.decision.domain.model.commands.submit_secure_query_command import (
    SubmitSecureQueryCommand,
)
from tests.conftest import (
    SAMPLES,
    SentinelTestContext,
    TimeoutFakeSecurityClient,
    TimingOutFakeGenerationClient,
)

SCENARIOS = json.loads((SAMPLES / "prompt-scenarios.json").read_text(encoding="utf-8"))["scenarios"]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[item["id"] for item in SCENARIOS])
@pytest.mark.asyncio
async def test_prompt_scenario_behaves_as_declared(
    context: SentinelTestContext,
    scenario: dict,
) -> None:
    if scenario["simulate"] == "analysis_timeout":
        context.security_client = TimeoutFakeSecurityClient()
    if scenario["simulate"] == "generation_timeout":
        context.generation_client = TimingOutFakeGenerationClient()

    document_content = (
        context.sample_bytes(scenario["document"]) if scenario["document"] else None
    )

    result = await context.secure_query_service().handle_submit_secure_query(
        SubmitSecureQueryCommand(
            prompt=scenario["prompt"],
            document_filename=scenario["document"],
            document_mime_type="application/json" if document_content else None,
            document_content=document_content,
        )
    )

    interaction = result.interaction
    assert interaction.decision.value == scenario["expected_decision"]
    assert interaction.generation_status.value == scenario["expected_generation"]

    found_types = {finding.finding_type for finding in interaction.masked_findings}
    assert set(scenario["expected_finding_types"]).issubset(found_types)

    if scenario["expected_decision"] == "blocked":
        assert result.answer is None
        assert context.generation_client.calls == []
    if scenario["expected_generation"] == "succeeded":
        assert result.answer is not None
    if scenario["expected_generation"] == "failed":
        assert result.answer is None
        assert interaction.generation_error


@pytest.mark.asyncio
async def test_no_scenario_ever_leaks_its_raw_values(context: SentinelTestContext) -> None:
    raw_values = (
        "SuperSecret123",
        "sk-proj4Xm2QpLd8Rt6VbNc1Zk9WsYh3Ge7Uf5Ja",
        "4539459532651916",
        "ana.gomez@example.com",
    )
    service = context.secure_query_service()

    dumped = ""
    for scenario in SCENARIOS:
        if scenario["simulate"]:
            continue
        document_content = (
            context.sample_bytes(scenario["document"]) if scenario["document"] else None
        )
        result = await service.handle_submit_secure_query(
            SubmitSecureQueryCommand(
                prompt=scenario["prompt"],
                document_filename=scenario["document"],
                document_mime_type="application/json" if document_content else None,
                document_content=document_content,
            )
        )
        dumped += json.dumps(
            {
                "reference": result.interaction.content_reference,
                "reason": result.interaction.reason,
                "findings": [
                    finding.masked_evidence for finding in result.interaction.masked_findings
                ],
            },
            ensure_ascii=False,
        )

    for raw_value in raw_values:
        assert raw_value not in dumped
