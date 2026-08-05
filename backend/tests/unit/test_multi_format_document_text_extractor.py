from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from app.analysis.domain.exceptions import AnalysisModelUnavailableError
from app.analysis.domain.model.valueobjects.vision_extraction_result import (
    VisionExtractionResult,
)
from app.analysis.infrastructure.text_extraction.multi_format_document_text_extractor import (
    MultiFormatDocumentTextExtractor,
)
from app.documents.domain.exceptions import UnsupportedDocumentTypeError


class RecordingVisionClient:
    model_name = "fake-vision"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def extract(
        self, *, image_content: bytes, mime_type: str, reference_label: str
    ) -> VisionExtractionResult:
        assert image_content
        self.calls.append((mime_type, reference_label))
        return VisionExtractionResult(
            visible_text="Correo visible: demo@example.com",
            visual_summary="Captura de una ficha de contacto.",
            document_type="contact_card",
            model_name=self.model_name,
        )


class UnavailableVisionClient(RecordingVisionClient):
    async def extract(self, **kwargs) -> VisionExtractionResult:
        del kwargs
        raise AnalysisModelUnavailableError("vision model unavailable")


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color="white").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_extracts_json_without_calling_vision() -> None:
    vision = RecordingVisionClient()
    extractor = MultiFormatDocumentTextExtractor(vision)

    result = await extractor.extract_content(
        b'{"project": "Sentinel"}', "application/json", "summary.json"
    )

    assert result == {"project": "Sentinel"}
    assert vision.calls == []


@pytest.mark.asyncio
async def test_image_content_comes_from_mandatory_local_vision() -> None:
    vision = RecordingVisionClient()
    extractor = MultiFormatDocumentTextExtractor(vision)

    result = await extractor.extract_content(_png_bytes(), "image/png", "contact.png")

    assert result["visible_text"] == "Correo visible: demo@example.com"
    assert result["vision_model"] == "fake-vision"
    assert vision.calls == [("image/png", "contact.png")]


@pytest.mark.asyncio
async def test_image_is_not_analyzable_when_local_vision_is_unavailable() -> None:
    extractor = MultiFormatDocumentTextExtractor(UnavailableVisionClient())

    with pytest.raises(AnalysisModelUnavailableError):
        await extractor.extract_content(_png_bytes(), "image/png", "contact.png")


@pytest.mark.asyncio
async def test_formats_beyond_json_and_images_are_rejected() -> None:
    extractor = MultiFormatDocumentTextExtractor(RecordingVisionClient())

    with pytest.raises(UnsupportedDocumentTypeError):
        await extractor.extract_content(b"%PDF-1.4", "application/pdf", "report.pdf")
