from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.decision.interfaces.rest.resources.secure_interaction_resource import (
    SecureInteractionResource,
)


class AssistantAnswerResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(description="Answer produced by the local model for the allowed query")
    model_name: str = Field(description="Model that produced the answer", examples=["llama3.2:3b"])
    generated_at: datetime = Field(description="Answer generation timestamp")


class SecureQueryResponse(BaseModel):
    """
    Result of one secure query.

    `answer` is present only when the decision was allowed and the person
    actually asked something. It is returned here and not stored.
    """

    model_config = ConfigDict(extra="forbid")

    interaction: SecureInteractionResource
    answer: AssistantAnswerResource | None = Field(
        default=None,
        description="Present only when the content was allowed and a question was submitted",
    )
