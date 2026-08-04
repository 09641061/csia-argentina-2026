from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.analysis.interfaces.rest.resources.analysis_finding_resource import (
    AnalysisFindingResource,
)


class DocumentAnalysisResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(description="Analysis execution identifier", examples=[1])
    document_id: int = Field(
        description="Associated document identifier", examples=[12]
    )
    source_filename: str = Field(
        description="Original JSON filename", examples=["customer-export.json"]
    )
    source_mime_type: str = Field(
        description="Source MIME type", examples=["application/json"]
    )
    source_size_bytes: int = Field(
        description="Approximate source size in bytes", examples=[245678]
    )
    status: str = Field(description="Analysis execution status", examples=["completed"])
    risk_level: str | None = Field(
        default=None, description="Final risk; null when execution failed or is running"
    )
    secrets_risk: str | None = Field(
        default=None, description="Credential and secret risk track"
    )
    personal_data_risk: str | None = Field(
        default=None, description="Personal-data risk track"
    )
    confidence: str | None = Field(
        default=None, description="Confidence in the final interpretation"
    )
    tampering_suspected: bool = Field(description="Prompt manipulation was detected")
    data_categories: list[str] = Field(
        description="Normalized categories detected in the document"
    )
    estimated_subjects: str = Field(
        description="Estimated number of affected people", examples=["6-100"]
    )
    summary: str = Field(description="Short reviewer-oriented result")
    rationale: str = Field(description="Safe evidence trail without source values")
    explanation: str = Field(description="Combined human-readable explanation")
    model_name: str = Field(
        description="Ollama model used for interpretation", examples=["llama3.2:3b"]
    )
    findings: list[AnalysisFindingResource] = Field(
        description="Safe deterministic findings"
    )
    content_truncated: bool = Field(
        description="The compact context represented a larger document"
    )
    has_sanitized_content: bool = Field(
        description="A sanitized JSON representation is available"
    )
    error_message: str | None = Field(
        default=None, description="Safe failure message when status is failed"
    )
    analyzed_at: datetime | None = Field(
        default=None, description="Successful completion timestamp"
    )
    created_at: datetime = Field(description="Execution creation timestamp")
    updated_at: datetime = Field(description="Execution last update timestamp")
