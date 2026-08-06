"""
The ten synthetic datasets run end to end through the real pipeline.

Only the security model is a fake, and it is a conservative one: it always
answers "low", so every risk asserted here was produced by the deterministic
rules alone.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy import select

from app.analysis.domain.exceptions import (
    AnalysisExecutionError,
    AnalysisModelInvalidResponseError,
)
from app.analysis.domain.model.commands.analyze_document_command import AnalyzeDocumentCommand
from app.analysis.domain.model.valueobjects.analysis_status import AnalysisStatus
from app.analysis.domain.model.valueobjects.analyzed_content_type import AnalyzedContentType
from app.analysis.infrastructure.persistence.sqlalchemy.models.security_analysis_model import (
    SecurityAnalysisModel,
)
from app.documents.domain.model.commands.create_document_command import CreateDocumentCommand
from tests.conftest import (
    SAMPLES,
    CrashingFakeSecurityClient,
    InvalidResponseFakeSecurityClient,
    ClaudeTestContext,
)


async def register_sample(context: ClaudeTestContext, filename: str) -> int:
    document = await context.document_command_service().handle_create_document(
        CreateDocumentCommand(
            original_filename=filename,
            mime_type="application/json",
            content=context.sample_bytes(filename),
        )
    )
    return document.id or 0


@pytest.mark.asyncio
async def test_all_datasets_run_through_pipeline_and_history(
    context: ClaudeTestContext,
) -> None:
    manifest = json.loads((SAMPLES / "expected-results.json").read_text(encoding="utf-8"))
    service = context.analysis_command_service()
    analyses = []
    document_ids = []

    for expected in manifest["datasets"]:
        document_id = await register_sample(context, expected["file"])
        analysis = await service.handle_analyze_document(
            AnalyzeDocumentCommand(document_id=document_id)
        )
        document_ids.append(document_id)
        analyses.append(analysis)

        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.content_type == AnalyzedContentType.DOCUMENT
        assert analysis.risk_level.value in expected["expected_risk"]
        assert len(analysis.findings) >= expected["minimum_findings"]
        assert set(expected["expected_finding_types"]).issubset(
            {finding.finding_type.value for finding in analysis.findings}
        )
        assert set(expected["expected_categories"]).issubset(set(analysis.data_categories))
        assert analysis.tampering_suspected is expected["tampering_expected"]

    page, total = await context.analysis_repository().list(page=1, page_size=4)
    assert total == 10
    assert len(page) == 4

    end_analysis = analyses[-1]
    last_record_index = (
        len(json.loads((SAMPLES / "sample-10-finding-at-end.json").read_text("utf-8"))["records"])
        - 1
    )
    assert any(
        finding.json_path.startswith(f"$.records[{last_record_index}]")
        for finding in end_analysis.findings
    )
    assert end_analysis.content_truncated is True

    second_run = await service.handle_analyze_document(
        AnalyzeDocumentCommand(document_id=document_ids[0])
    )
    latest = await context.analysis_repository().find_latest_by_document_id(document_ids[0])
    _, total_after_reanalysis = await context.analysis_repository().list(page=1, page_size=100)

    assert latest.id == second_run.id
    assert second_run.id != analyses[0].id
    assert total_after_reanalysis == 11


@pytest.mark.asyncio
async def test_persistence_never_contains_complete_secrets(
    context: ClaudeTestContext,
) -> None:
    document_id = await register_sample(context, "sample-03-credentials-dump.json")
    analysis = await context.analysis_command_service().handle_analyze_document(
        AnalyzeDocumentCommand(document_id=document_id)
    )

    model = await context.session.scalar(
        select(SecurityAnalysisModel).where(SecurityAnalysisModel.id == analysis.id)
    )
    persisted = json.dumps(
        {
            "findings": model.findings,
            "summary": model.summary,
            "rationale": model.rationale,
            "masked_preview": model.masked_preview,
            "content_reference": model.content_reference,
        }
    )

    complete_values = (
        "S3nt1nel-Pr0d-2026!",
        "sk-proj4Xm2QpLd8Rt6VbNc1Zk9WsYh3Ge7Uf5Ja",
        "AKIA4XM2QPLD8RT6VBNC",
        "ghp_7f2c1b8d9a4e5f6c7d8e",
        "DemoService-00-Pass!",
    )
    for complete_value in complete_values:
        assert complete_value not in persisted


@pytest.mark.asyncio
async def test_no_sanitized_copy_of_the_document_is_ever_stored(
    context: ClaudeTestContext,
) -> None:
    document_id = await register_sample(context, "sample-03-credentials-dump.json")
    await context.analysis_command_service().handle_analyze_document(
        AnalyzeDocumentCommand(document_id=document_id)
    )

    columns = set(SecurityAnalysisModel.__table__.columns.keys())
    assert "sanitized_content" not in columns
    assert "raw_content" not in columns


@pytest.mark.asyncio
async def test_invalid_model_response_persists_a_failed_execution_without_low_risk(
    context: ClaudeTestContext,
) -> None:
    context.security_client = InvalidResponseFakeSecurityClient()
    document_id = await register_sample(context, "sample-01-clean-inventory.json")

    with pytest.raises(AnalysisModelInvalidResponseError):
        await context.analysis_command_service().handle_analyze_document(
            AnalyzeDocumentCommand(document_id=document_id)
        )

    failed = await context.analysis_repository().find_latest_by_document_id(document_id)
    assert failed is not None
    assert failed.status == AnalysisStatus.FAILED
    assert failed.risk_level is None
    assert failed.secrets_risk is None
    assert failed.personal_data_risk is None
    assert failed.error_message == "El analizador de seguridad no devolvió una respuesta válida."


@pytest.mark.asyncio
async def test_unexpected_exception_never_leaves_the_execution_running(
    context: ClaudeTestContext,
) -> None:
    context.security_client = CrashingFakeSecurityClient()
    document_id = await register_sample(context, "sample-01-clean-inventory.json")

    with pytest.raises(AnalysisExecutionError):
        await context.analysis_command_service().handle_analyze_document(
            AnalyzeDocumentCommand(document_id=document_id)
        )

    stored = await context.analysis_repository().find_latest_by_document_id(document_id)
    assert stored is not None
    assert stored.status == AnalysisStatus.FAILED
    assert stored.risk_level is None

    # A stuck RUNNING row used to make every later analysis of the same document
    # fail forever; a second attempt must still be possible.
    context.security_client = None
    from tests.conftest import ConservativeFakeSecurityClient

    context.security_client = ConservativeFakeSecurityClient()
    retried = await context.analysis_command_service().handle_analyze_document(
        AnalyzeDocumentCommand(document_id=document_id)
    )
    assert retried.status == AnalysisStatus.COMPLETED


@pytest.mark.asyncio
async def test_invalid_json_and_unsupported_mime_types_are_rejected_at_intake(
    context: ClaudeTestContext,
) -> None:
    from app.documents.domain.exceptions import (
        InvalidDocumentContentError,
        UnsupportedDocumentTypeError,
    )

    with pytest.raises(InvalidDocumentContentError):
        await context.document_command_service().handle_create_document(
            CreateDocumentCommand(
                original_filename="broken.json",
                mime_type="application/json",
                content=b"{not valid json",
            )
        )

    with pytest.raises(InvalidDocumentContentError):
        await context.document_command_service().handle_create_document(
            CreateDocumentCommand(
                original_filename="scalar.json",
                mime_type="application/json",
                content=b'"just a string"',
            )
        )

    with pytest.raises(UnsupportedDocumentTypeError):
        await context.document_command_service().handle_create_document(
            CreateDocumentCommand(
                original_filename="notes.txt",
                mime_type="text/plain",
                content=b"plain text",
            )
        )
