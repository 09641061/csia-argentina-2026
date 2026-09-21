from pydantic import BaseModel, ConfigDict, Field


class SecureQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=3, max_length=8000)
