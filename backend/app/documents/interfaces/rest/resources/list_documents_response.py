from pydantic import BaseModel, ConfigDict, Field

from app.documents.interfaces.rest.resources.document_resource import DocumentResource


class DocumentPageMetadataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(description="Current page number", examples=[1])
    page_size: int = Field(description="Page size used for the query", examples=[20])
    total: int = Field(description="Total number of documents", examples=[42])


class ListDocumentsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DocumentResource] = Field(description="Documents in the current page")
    page: DocumentPageMetadataResponse

