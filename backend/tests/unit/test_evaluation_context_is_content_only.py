"""
What the reviewers are allowed to judge.

Two bugs made benign files look dangerous, and both came from the same mistake:
something that is not the content ended up inside the evidence. A file called
`messi-<insult>.jpg` was blocked while the identical image with a neutral name
passed, and a photo was blocked for carrying a description longer than the sample
budget. These tests pin down the boundary so neither can come back.
"""

from __future__ import annotations

import json

import pytest

from app.analysis.application.internal.services.content_sanitization_service import (
    ContentSanitizationService,
)
from app.analysis.application.internal.services.document_structure_summarizer import (
    DocumentStructureSummarizer,
)
from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.valueobjects.vision_extraction_result import (
    VisionExtractionResult,
)
from app.documents.domain.model.commands.create_document_command import (
    CreateDocumentCommand,
)
from tests.conftest import SentinelTestContext

INSULTING_FILENAME = "messi-hijo-de-puta-culo-feo-mierda.json"
LONG_VISUAL_SUMMARY = (
    "A photograph of a golden retriever dog sitting on green grass in a park on a sunny "
    "day. The dog is facing the camera with its tongue out. No text, documents or "
    "identifying information are visible anywhere in the picture."
)


@pytest.mark.asyncio
async def test_filename_never_reaches_the_security_model(
    context: SentinelTestContext,
) -> None:
    """
    Renaming a file must not change its verdict.

    The uploader picks the filename, so it is untrusted metadata that describes
    nothing about the bytes. When it travelled into the evaluation context the
    local model judged the name instead of the content and returned a higher risk
    for an identical document.
    """

    document = await context.document_command_service().handle_create_document(
        CreateDocumentCommand(
            original_filename=INSULTING_FILENAME,
            mime_type="application/json",
            content=json.dumps({"project": "Sentinel", "stage": "demo"}).encode(
                "utf-8"
            ),
        )
    )

    analysis = await context.analysis_command_service().handle_analyze_document(
        AnalyzeDocumentCommand(document_id=document.id or 0)
    )

    evaluation = context.security_client.calls[-1]
    serialized = json.dumps(evaluation.to_prompt_payload(), ensure_ascii=False).lower()
    for word in ("messi", "hijo", "puta", "culo", "feo", "mierda"):
        assert word not in serialized

    # The audit trail still records which file was reviewed.
    assert analysis.content_reference


@pytest.mark.asyncio
async def test_analysis_is_identical_for_a_renamed_document(
    context: SentinelTestContext,
) -> None:
    payload = json.dumps({"project": "Sentinel", "stage": "demo"}).encode("utf-8")
    service = context.analysis_command_service()
    command_service = context.document_command_service()

    neutral = await command_service.handle_create_document(
        CreateDocumentCommand(
            original_filename="foto.json", mime_type="application/json", content=payload
        )
    )
    insulting = await command_service.handle_create_document(
        CreateDocumentCommand(
            original_filename=INSULTING_FILENAME,
            mime_type="application/json",
            content=payload,
        )
    )

    first = await service.handle_analyze_document(
        AnalyzeDocumentCommand(document_id=neutral.id or 0)
    )
    second = await service.handle_analyze_document(
        AnalyzeDocumentCommand(document_id=insulting.id or 0)
    )

    assert first.risk_level == second.risk_level
    assert first.tampering_suspected == second.tampering_suspected
    assert len(first.findings) == len(second.findings)

    neutral_context, insulting_context = context.security_client.calls[-2:]
    assert neutral_context.to_prompt_payload() == insulting_context.to_prompt_payload()


def test_a_long_image_description_is_not_a_truncated_document() -> None:
    """
    A picture's description is prose, not a cut-off export.

    `truncated` tells the classifier that scale may be hidden, and its prompt
    treats a truncated document as never automatically clean. A normal visual
    summary used to trip that flag just by exceeding the per-value sample budget,
    which is how a photo of a dog ended up BLOCKED.
    """

    extracted = VisionExtractionResult(
        visible_text="",
        visual_summary=LONG_VISUAL_SUMMARY,
        document_type="Photograph",
        model_name="gemma3:4b",
    ).to_document_payload()

    summary = DocumentStructureSummarizer().summarize(
        content=extracted,
        sanitized_content=ContentSanitizationService().sanitize(extracted, []),
        findings=[],
        approximate_size_bytes=180_000,
    )

    assert summary.truncated is False
    assert any(LONG_VISUAL_SUMMARY in leaf for leaf in summary.safe_sample)


def test_a_document_whose_leaves_are_omitted_is_still_truncated() -> None:
    """The flag must keep firing where it means something: leaves left out."""

    content = {
        "records": [{"id": index, "note": f"row {index}"} for index in range(40)]
    }

    summary = DocumentStructureSummarizer().summarize(
        content=content,
        sanitized_content=ContentSanitizationService().sanitize(content, []),
        findings=[],
        approximate_size_bytes=4_096,
    )

    assert summary.truncated is True
    assert len(summary.safe_sample) < 80
