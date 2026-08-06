from pydantic import BaseModel, ConfigDict, Field

from app.documents.domain.model.valueobjects.tabular_document_content import TableCell


class DocumentTableResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: int = Field(gt=0, description="Document identifier", examples=[1])
    columns: list[str] = Field(description="Ordered column names for the frontend table")
    rows: list[dict[str, TableCell]] = Field(description="Normalized table rows")
    metadata: dict[str, TableCell] = Field(description="Top-level scalar document metadata")
    total_rows: int = Field(ge=0, description="Number of normalized rows", examples=[10])
