from pydantic import BaseModel, ConfigDict, Field

from app.documents.domain.model.valueobjects.document_status import DocumentStatus


class UpdateDocumentStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: DocumentStatus = Field(
        description="New document status",
        examples=[DocumentStatus.PROCESSING.value],
    )
    blocked_reason: str | None = Field(
        default=None,
        description="Reason for blocking the document, required when status is blocked",
        examples=["Contains secrets"],
    )
