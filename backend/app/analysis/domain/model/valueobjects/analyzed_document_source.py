from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalyzedDocumentSource:
    """
    Everything Analysis is allowed to know about a registered document.

    There is no URL and no storage path here: content is obtained through the
    Documents contract, which keeps the reading of bytes inside the controlled
    storage adapter and removes any chance of pointing the analysis at an
    arbitrary location.
    """

    document_id: int
    display_name: str
    mime_type: str
    size_bytes: int

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError("Document ID must be a positive number")
        if not self.display_name.strip():
            raise ValueError("Document display name is required")
        if not self.mime_type.strip():
            raise ValueError("Document MIME type is required")
        if self.size_bytes <= 0:
            raise ValueError("Document size must be a positive number")
