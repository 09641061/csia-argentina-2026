from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisionExtractionResult:
    """Ephemeral transcription produced by the trusted local vision model."""

    visible_text: str
    visual_summary: str
    document_type: str
    model_name: str

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError("The vision model name is required")
        if not self.visible_text.strip() and not self.visual_summary.strip():
            raise ValueError("The vision model returned no analyzable content")
        if len(self.visible_text) > 100_000 or len(self.visual_summary) > 4_000:
            raise ValueError("The vision extraction exceeded its safe output limit")
        if len(self.document_type) > 100:
            raise ValueError("The visual document type is too long")

    def to_document_payload(self) -> dict[str, object]:
        """
        What the image *contains*, and nothing else.

        The model name is pipeline metadata, not something the picture shows. It
        used to travel inside this payload and the reviewers treated it as part of
        the document, reporting `vision_model` as a data category and citing the
        model name as evidence. The analysis record already stores it.
        """

        return {
            "document_type": self.document_type.strip() or "unknown",
            "visible_text": self.visible_text.strip(),
            "visual_summary": self.visual_summary.strip(),
        }
