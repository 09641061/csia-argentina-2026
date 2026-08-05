from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUserResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(description="Authenticated local username")
