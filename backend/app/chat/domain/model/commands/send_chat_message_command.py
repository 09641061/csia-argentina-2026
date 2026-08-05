from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SendChatMessageCommand:
    prompt: str | None = None
    resource_filename: str | None = None
    resource_mime_type: str | None = None
    resource_content: bytes | None = None

    def __post_init__(self) -> None:
        has_prompt = bool((self.prompt or "").strip())
        has_resource = bool(self.resource_filename and self.resource_content)
        if not has_prompt and not has_resource:
            raise ValueError("At least a message or resource is required")
        if has_resource and not (self.resource_mime_type or "").strip():
            raise ValueError("Resource MIME type is required")
