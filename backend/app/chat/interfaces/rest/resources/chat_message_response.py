from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(
        min_length=1,
        description="Assistant response generated for the authorized message",
        examples=["4"],
    )
    conversation_id: int = Field(
        gt=0,
        description="Conversation created automatically or continued by this message",
    )
    model_name: str = Field(
        min_length=1,
        description="Local assistant model that generated the response",
        examples=["gemma3:4b"],
    )
    generated_at: datetime = Field(description="Answer generation timestamp")
