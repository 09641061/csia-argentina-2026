from pydantic import BaseModel, ConfigDict, Field


class AnalyzePromptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(
        min_length=1,
        max_length=8000,
        description="Free-text query to review before it can reach the local AI",
        examples=["Explícame las ventajas de una arquitectura orientada a eventos."],
    )
