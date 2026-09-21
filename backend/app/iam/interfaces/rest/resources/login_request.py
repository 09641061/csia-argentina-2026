from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9._-]+$",
        description="Account username",
        examples=["claude.demo"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Account password",
        examples=["DemoSecure2026"],
    )
