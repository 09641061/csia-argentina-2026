from pydantic import BaseModel, ConfigDict, Field


class SanitizedDocumentContentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: int = Field(description="Analysis execution identifier", examples=[1])
    document_id: int = Field(
        description="Associated document identifier", examples=[12]
    )
    sanitized_content: dict[str, object] | list[object] = Field(
        description="Independent JSON representation with sensitive values redacted or masked"
    )
