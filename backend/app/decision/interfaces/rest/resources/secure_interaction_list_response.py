from pydantic import BaseModel, ConfigDict, Field

from app.decision.interfaces.rest.resources.secure_interaction_resource import (
    SecureInteractionResource,
)


class SecureInteractionPageMetadataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(description="Current page number", examples=[1])
    page_size: int = Field(description="Page size used for the query", examples=[20])
    total: int = Field(description="Total number of interactions", examples=[12])


class SecureInteractionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SecureInteractionResource] = Field(
        description="Audited interactions in the current page"
    )
    page: SecureInteractionPageMetadataResponse = Field(description="Pagination metadata")
