from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sentinel_ai_guard",
        alias="DATABASE_URL",
    )
    upload_dir: str = Field(default="storage/documents", alias="UPLOAD_DIR")
    max_document_size_mb: int = Field(default=20, alias="MAX_DOCUMENT_SIZE_MB")
    allowed_mime_types: str = Field(
        default="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/json",
        alias="ALLOWED_MIME_TYPES",
    )

    @property
    def allowed_mime_type_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_mime_types.split(",") if item.strip()]

    @property
    def max_document_size_bytes(self) -> int:
        return self.max_document_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

