from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64, description="Account username", examples=["admin"])
    password: str = Field(min_length=1, max_length=128, description="Account password", examples=["admin"])
