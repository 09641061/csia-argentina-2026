from pydantic import BaseModel, ConfigDict, Field


class AnalysisFindingResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_type: str = Field(description="Type of finding", examples=["api_key"])
    severity: str = Field(description="Finding severity", examples=["high"])
    title: str = Field(description="Short finding title", examples=["API key detected"])
    description: str = Field(description="Detailed finding description", examples=["The document contains a token-like value."])
    evidence: str = Field(description="Matching evidence extracted from the document", examples=["sk-abc123..."])

