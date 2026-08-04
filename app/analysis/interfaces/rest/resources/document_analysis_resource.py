from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.analysis.interfaces.rest.resources.analysis_finding_resource import AnalysisFindingResource


class DocumentAnalysisResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Analysis identifier", examples=[1])
    document_id: int = Field(description="Associated document identifier", examples=[12])
    source_filename: str = Field(description="Original filename", examples=["contract.pdf"])
    source_mime_type: str = Field(description="Original MIME type", examples=["application/pdf"])
    source_document_url: str = Field(description="Source document URL", examples=["https://res.cloudinary.com/..."])
    risk_level: str = Field(description="Final analysis risk level", examples=["high"])
    explanation: str = Field(description="Short explanation of the analysis result")
    model_name: str = Field(description="Ollama model used for interpretation", examples=["llama3.2:3b"])
    findings: list[AnalysisFindingResource] = Field(description="Rule-based findings produced by the analysis")
    analyzed_at: datetime = Field(description="Analysis timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

