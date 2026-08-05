from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(description="Bearer token for protected API operations")
    token_type: str = Field(
        description="HTTP authentication scheme", examples=["bearer"]
    )
    expires_at: datetime = Field(description="UTC expiration timestamp")
    username: str = Field(description="Normalized local account username")
