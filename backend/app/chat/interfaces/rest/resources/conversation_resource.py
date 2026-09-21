from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationSummaryResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationMessageResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    role: str
    content: str
    attachment_url: str | None = None
    attachment_name: str | None = None
    attachment_mime_type: str | None = None
    created_at: datetime


class ConversationDetailResource(ConversationSummaryResource):
    messages: list[ConversationMessageResource]
    message_page: int
    message_page_size: int
