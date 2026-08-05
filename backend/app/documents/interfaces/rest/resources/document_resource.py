from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResource(BaseModel):
    """
    Public view of a registered document.

    The internal storage reference is intentionally absent: the API exposes the
    identifier only, so no local path or remote URL ever reaches a client.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(description="Document identifier", examples=[1])
    display_name: str = Field(
        description="Safe, masked label derived from the uploaded filename",
        examples=["inventario-servicios.json"],
    )
    mime_type: str = Field(
        description="Validated document MIME type",
        examples=["application/json"],
    )
    size_bytes: int = Field(description="Document size in bytes", examples=[24567])
    status: str = Field(description="Current document status", examples=["uploaded"])
    created_at: datetime = Field(description="Document creation timestamp")
    updated_at: datetime = Field(description="Document last update timestamp")
    analyzed_at: datetime | None = Field(
        default=None, description="Timestamp of the security review outcome"
    )
    blocked_reason: str | None = Field(
        default=None, description="Safe reason why the document was blocked"
    )
