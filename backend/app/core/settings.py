from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Runtime configuration for Sentinel AI Guard.

    Local, private storage is the default so an uploaded document is never sent
    to a third party before the security review decides whether it is safe.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sentinel_ai_guard",
        alias="DATABASE_URL",
    )

    frontend_origin: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="FRONTEND_ORIGIN",
        description="Comma separated list of browser origins allowed by CORS",
    )

    document_storage_backend: str = Field(
        default="local",
        alias="DOCUMENT_STORAGE_BACKEND",
        description="Storage adapter used by Documents: local or cloudinary",
    )
    document_storage_dir: str = Field(
        default="storage/documents",
        alias="DOCUMENT_STORAGE_DIR",
        description="Private directory used by the local storage adapter",
    )
    max_document_size_mb: int = Field(
        default=5,
        alias="MAX_DOCUMENT_SIZE_MB",
        gt=0,
        le=100,
    )

    cloudinary_cloud_name: str = Field(default="", alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", alias="CLOUDINARY_API_SECRET")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    ollama_security_model: str = Field(
        default="llama3.2:3b",
        alias="OLLAMA_SECURITY_MODEL",
        description="Model used only for the contextual security evaluation",
    )
    ollama_security_timeout_seconds: int = Field(
        default=120,
        alias="OLLAMA_SECURITY_TIMEOUT_SECONDS",
        gt=0,
    )
    ollama_security_context_tokens: int = Field(
        default=8192,
        alias="OLLAMA_SECURITY_CONTEXT_TOKENS",
        gt=0,
    )
    ollama_security_max_output_tokens: int = Field(
        default=300,
        alias="OLLAMA_SECURITY_MAX_OUTPUT_TOKENS",
        gt=0,
    )

    ollama_discovery_model: str = Field(
        default="gemma3:4b",
        alias="OLLAMA_DISCOVERY_MODEL",
        description="Mandatory model that classifies unmasked extracted content locally",
    )
    ollama_discovery_timeout_seconds: int = Field(
        default=180,
        alias="OLLAMA_DISCOVERY_TIMEOUT_SECONDS",
        gt=0,
    )
    ollama_discovery_context_tokens: int = Field(
        default=8192,
        alias="OLLAMA_DISCOVERY_CONTEXT_TOKENS",
        gt=0,
    )
    ollama_discovery_max_output_tokens: int = Field(
        default=200,
        alias="OLLAMA_DISCOVERY_MAX_OUTPUT_TOKENS",
        gt=0,
    )
    ollama_discovery_max_input_chars: int = Field(
        default=24_000,
        alias="OLLAMA_DISCOVERY_MAX_INPUT_CHARS",
        gt=0,
    )

    ollama_vision_model: str = Field(
        default="gemma3:4b",
        alias="OLLAMA_VISION_MODEL",
        description="Mandatory local model for images and scanned PDF pages",
    )
    ollama_vision_timeout_seconds: int = Field(
        default=180,
        alias="OLLAMA_VISION_TIMEOUT_SECONDS",
        gt=0,
    )
    ollama_vision_context_tokens: int = Field(
        default=8192,
        alias="OLLAMA_VISION_CONTEXT_TOKENS",
        gt=0,
    )
    ollama_vision_max_output_tokens: int = Field(
        default=1200,
        alias="OLLAMA_VISION_MAX_OUTPUT_TOKENS",
        gt=0,
    )

    ollama_generation_model: str = Field(
        default="llama3.2:3b",
        alias="OLLAMA_GENERATION_MODEL",
        description="Model used only to answer already allowed content",
    )
    ollama_generation_timeout_seconds: int = Field(
        default=180,
        alias="OLLAMA_GENERATION_TIMEOUT_SECONDS",
        gt=0,
    )
    ollama_generation_context_tokens: int = Field(
        default=8192,
        alias="OLLAMA_GENERATION_CONTEXT_TOKENS",
        gt=0,
    )
    ollama_generation_max_output_tokens: int = Field(
        default=800,
        alias="OLLAMA_GENERATION_MAX_OUTPUT_TOKENS",
        gt=0,
    )
    ollama_generation_max_document_chars: int = Field(
        default=24000,
        alias="OLLAMA_GENERATION_MAX_DOCUMENT_CHARS",
        gt=0,
        description="Allowed document characters that still fit in the answer context",
    )

    prompt_max_length: int = Field(default=8000, alias="PROMPT_MAX_LENGTH", gt=0)
    prompt_min_length: int = Field(default=3, alias="PROMPT_MIN_LENGTH", gt=0)

    @field_validator("document_storage_backend")
    @classmethod
    def validate_storage_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"local", "cloudinary"}:
            raise ValueError("DOCUMENT_STORAGE_BACKEND must be 'local' or 'cloudinary'")
        return normalized

    @property
    def max_document_size_bytes(self) -> int:
        return self.max_document_size_mb * 1024 * 1024

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def document_storage_root(self) -> Path:
        configured = Path(self.document_storage_dir)
        if configured.is_absolute():
            return configured
        return PROJECT_ROOT / configured


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
