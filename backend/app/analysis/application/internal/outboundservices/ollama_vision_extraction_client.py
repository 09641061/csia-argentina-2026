from typing import Protocol

from app.analysis.domain.model.valueobjects.vision_extraction_result import (
    VisionExtractionResult,
)


class OllamaVisionExtractionClient(Protocol):
    """Local multimodal AI used to understand uploaded images."""

    @property
    def model_name(self) -> str: ...

    async def extract(
        self,
        *,
        image_content: bytes,
        mime_type: str,
        reference_label: str,
    ) -> VisionExtractionResult: ...
