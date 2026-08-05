from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.analysis.interfaces.rest.resources.analysis_finding_resource import (
    AnalysisFindingResource,
)


class SecurityAnalysisResource(BaseModel):
    """
    Public view of one security review.

    It carries no original prompt, no document content and no sanitized copy:
    only the fingerprint, the masked preview, the masked findings and the risk
    assessment.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(description="Analysis execution identifier", examples=[1])
    content_type: str = Field(
        description="What was reviewed: prompt or document", examples=["document"]
    )
    document_id: int | None = Field(
        default=None, description="Associated document identifier, when applicable", examples=[12]
    )
    content_reference: str = Field(
        description="Safe, masked label of the reviewed content",
        examples=["inventario-servicios.json"],
    )
    content_fingerprint: str = Field(
        description="SHA-256 digest of the reviewed content, for traceability without storing it"
    )
    content_length: int = Field(
        description="Characters for a prompt, bytes for a document", examples=[24567]
    )
    masked_preview: str = Field(description="Masked preview of the reviewed content")
    status: str = Field(description="Analysis execution status", examples=["completed"])
    risk_level: str | None = Field(
        default=None, description="Final risk; null when the execution failed or is running"
    )
    secrets_risk: str | None = Field(default=None, description="Credential and secret risk track")
    personal_data_risk: str | None = Field(default=None, description="Personal-data risk track")
    confidence: str | None = Field(default=None, description="Confidence in the interpretation")
    tampering_suspected: bool = Field(description="Prompt manipulation was detected")
    data_categories: list[str] = Field(description="Normalized detected categories")
    estimated_subjects: str = Field(
        description="Estimated number of affected people", examples=["6-100"]
    )
    summary: str = Field(description="Short reviewer-oriented result")
    rationale: str = Field(description="Safe evidence trail without source values")
    explanation: str = Field(description="Combined human-readable explanation")
    model_name: str = Field(
        description="Ollama model used for the security evaluation", examples=["gemma3:4b"]
    )
    findings: list[AnalysisFindingResource] = Field(description="Masked deterministic findings")
    content_truncated: bool = Field(
        description="The compact context represented a larger content"
    )
    error_message: str | None = Field(
        default=None, description="Safe failure message when the status is failed"
    )
    analyzed_at: datetime | None = Field(
        default=None, description="Successful completion timestamp"
    )
    created_at: datetime = Field(description="Execution creation timestamp")
    updated_at: datetime = Field(description="Execution last update timestamp")
