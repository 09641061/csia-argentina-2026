from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Document identifier", examples=[1])
    owner_user_id: int = Field(description="Owner user identifier", examples=[7])
    name: str = Field(description="Business document name", examples=["Customer export Q3 2026"])
    original_filename: str = Field(description="Original uploaded filename", examples=["customer-export.json"])
    mime_type: str = Field(description="Document MIME type, always application/json", examples=["application/json"])
    size_bytes: int = Field(description="Document size in bytes", examples=[245678])
    storage_path: str = Field(description="Internal storage path", examples=["storage/documents/abc123.json"])
    status: str = Field(description="Current document status", examples=["uploaded"])
    created_at: datetime = Field(description="Document creation timestamp")
    updated_at: datetime = Field(description="Document last update timestamp")
    analyzed_at: datetime | None = Field(default=None, description="Document analysis timestamp")
    blocked_reason: str | None = Field(default=None, description="Reason why the document was blocked")

