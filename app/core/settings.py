from functools import lru_cache
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sentinel_ai_guard",
        alias="DATABASE_URL",
    )
    cloudinary_cloud_name: str = Field(default="", alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", alias="CLOUDINARY_API_SECRET")
    allowed_mime_types: str = Field(
        default="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/json",
        alias="ALLOWED_MIME_TYPES",
    )

    DEFAULT_MAX_DOCUMENT_SIZE_MB: ClassVar[int] = 20

    @property
    def allowed_mime_type_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_mime_types.split(",") if item.strip()]

    @property
    def max_document_size_bytes(self) -> int:
        return self.DEFAULT_MAX_DOCUMENT_SIZE_MB * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
