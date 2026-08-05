from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubmitSecureQueryCommand:
    """
    A single secure query: a prompt, a document, or both.

    At least one of the two must be present; a request with neither has nothing
    to review and nothing to answer.
    """

    prompt: str | None = None
    document_filename: str | None = None
    document_mime_type: str | None = None
    document_content: bytes | None = None

    def __post_init__(self) -> None:
        has_prompt = bool((self.prompt or "").strip())
        has_document = bool(self.document_content)
        if not has_prompt and not has_document:
            raise ValueError("Se necesita al menos una consulta o un documento.")
        if has_document and not (self.document_mime_type or "").strip():
            raise ValueError("El documento adjunto necesita un tipo MIME.")

    @property
    def has_prompt(self) -> bool:
        return bool((self.prompt or "").strip())

    @property
    def has_document(self) -> bool:
        return bool(self.document_content)
