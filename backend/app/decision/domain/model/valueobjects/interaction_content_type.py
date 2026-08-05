from enum import StrEnum


class InteractionContentType(StrEnum):
    PROMPT = "prompt"
    DOCUMENT = "document"
    PROMPT_WITH_DOCUMENT = "prompt_with_document"
