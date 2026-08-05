from pydantic import BaseModel, ConfigDict, Field

from app.analysis.interfaces.rest.resources.analysis_finding_resource import (
    AnalysisFindingResource,
)


class AnalysisFindingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: int = Field(description="Analysis execution identifier", examples=[1])
    items: list[AnalysisFindingResource] = Field(
        description="Masked findings for this execution"
    )
