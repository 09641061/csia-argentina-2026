from pydantic import BaseModel, ConfigDict, Field

from app.analysis.interfaces.rest.resources.security_analysis_resource import (
    SecurityAnalysisResource,
)


class SecurityAnalysisPageMetadataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(description="Current page number", examples=[1])
    page_size: int = Field(description="Page size used for the query", examples=[20])
    total: int = Field(description="Total number of analyses", examples=[8])


class SecurityAnalysisListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SecurityAnalysisResource]
    page: SecurityAnalysisPageMetadataResponse
