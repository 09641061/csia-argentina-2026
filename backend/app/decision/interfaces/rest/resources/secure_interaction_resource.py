from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MaskedFindingResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: str = Field(description="Where the finding came from", examples=["prompt"])
    finding_type: str = Field(description="Type of sensitive data", examples=["api_key"])
    severity: str = Field(description="Deterministic severity", examples=["high"])
    title: str = Field(description="Short human-readable title")
    location: str = Field(
        description="Approximate location of the value", examples=["$.services[2].api_key"]
    )
    masked_evidence: str = Field(
        description="Masked evidence; the original value is never returned",
        examples=["sk-p*****************f5Ja"],
    )
    occurrences: int = Field(ge=1, description="Equivalent matches grouped in this finding")
    is_placeholder: bool = Field(description="The value looks like a placeholder or example")


class SecureInteractionResource(BaseModel):
    """
    Public view of one audited secure query.

    It exposes the verdict, the reason and masked evidence. It never exposes the
    submitted prompt or the generated answer.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(description="Interaction identifier", examples=[1])
    content_type: str = Field(
        description="Type of reviewed content", examples=["prompt"]
    )
    decision: str = Field(description="allowed or blocked", examples=["blocked"])
    reason_code: str = Field(
        description="Machine-readable reason", examples=["prompt_contains_sensitive_data"]
    )
    reason: str = Field(description="Human-readable reason in Spanish")
    content_reference: str = Field(
        description="Safe, masked label of what was reviewed",
        examples=["Consulta escrita"],
    )
    risk_level: str | None = Field(
        default=None, description="Highest risk across the reviews", examples=["high"]
    )
    prompt_analysis_id: int | None = Field(default=None, description="Prompt review identifier")
    data_categories: list[str] = Field(description="Types of information detected")
    masked_findings: list[MaskedFindingResource] = Field(description="Masked evidence")
    generation_status: str = Field(
        description="not_requested, skipped, succeeded or failed", examples=["succeeded"]
    )
    generation_model: str | None = Field(
        default=None, description="Model that produced the answer", examples=["gemma3:4b"]
    )
    generation_error: str | None = Field(
        default=None, description="Safe message when the answer could not be produced"
    )
    generated_at: datetime | None = Field(default=None, description="Answer generation timestamp")
    created_at: datetime = Field(description="Interaction timestamp")
