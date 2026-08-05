from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interaction_id: int = Field(gt=0, description="Audited interaction identifier", examples=[1])
    decision: str = Field(description="Authorization decision", examples=["allowed"])
    reason: str = Field(description="Safe explanation of the authorization decision")
    document_id: int | None = Field(default=None, description="Registered resource identifier")
    answer: str | None = Field(default=None, description="Generated answer when authorized")
    answer_model: str | None = Field(default=None, description="Model used for the answer")
    generated_at: datetime | None = Field(default=None, description="Answer generation timestamp")
