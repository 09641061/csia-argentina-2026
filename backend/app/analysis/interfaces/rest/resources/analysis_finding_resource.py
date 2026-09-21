from pydantic import BaseModel, ConfigDict, Field


class AnalysisFindingResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(
        description="Identifier local to this analysis", examples=["f3"]
    )
    finding_type: str = Field(
        description="Type of sensitive-data finding", examples=["api_key"]
    )
    severity: str = Field(
        description="Deterministic finding severity", examples=["high"]
    )
    title: str = Field(description="Short finding title", examples=["API key detected"])
    description: str = Field(description="Safe explanation without source values")
    json_path: str = Field(
        description="Approximate path of the value in the JSON",
        examples=["$.services[2].api_key"],
    )
    evidence: str = Field(
        description="Masked evidence; the original value is never returned",
        examples=["sk-p*******************************f5Ja"],
    )
    detection_method: str = Field(
        description="Rule or validation that produced the finding",
        examples=["recognized_credential_pattern"],
    )
    confidence: str = Field(
        description="Confidence in the deterministic finding", examples=["high"]
    )
    occurrences: int = Field(
        ge=1, description="Number of equivalent matches grouped in this finding"
    )
    data_category: str | None = Field(
        default=None, description="Normalized data category"
    )
    is_placeholder: bool = Field(
        description="Whether the value looks like a placeholder or documentation example"
    )
