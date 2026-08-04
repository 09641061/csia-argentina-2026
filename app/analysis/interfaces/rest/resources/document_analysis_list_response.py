from pydantic import BaseModel, ConfigDict, Field

from app.analysis.interfaces.rest.resources.document_analysis_resource import DocumentAnalysisResource


class DocumentAnalysisPageMetadataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(description="Current page number", examples=[1])
    page_size: int = Field(description="Page size used for the query", examples=[20])
    total: int = Field(description="Total number of analyses", examples=[8])


class DocumentAnalysisListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DocumentAnalysisResource]
    page: DocumentAnalysisPageMetadataResponse

