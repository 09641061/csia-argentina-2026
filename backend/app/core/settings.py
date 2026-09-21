from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Runtime configuration for Claude AI Guard.

    Environment-specific runtime configuration for the text-only MVP.
    """

    # Accept the backend-local file first, with the repository-level file as a
    # convenient fallback for local development. The backend-local settings
    # win when both files define the same variable.
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT.parent / ".env", PROJECT_ROOT / ".env"),
        extra="ignore",
        populate_by_name=True,
    )

    environment: str = Field(default="development", alias="ENVIRONMENT")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/claude_ai_guard",
        alias="DATABASE_URL",
    )

    frontend_origin: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="FRONTEND_ORIGIN",
        description="Comma separated list of browser origins allowed by CORS",
    )

    jwt_secret_key: str = Field(
        default="claude-local-development-key-change-before-deploy-2026",
        alias="JWT_SECRET_KEY",
        min_length=32,
        description="Stable secret used to sign local access tokens",
    )
    jwt_issuer: str = Field(
        default="claude-ai-guard", alias="JWT_ISSUER", min_length=1
    )
    jwt_audience: str = Field(
        default="claude-ai-guard-web",
        alias="JWT_AUDIENCE",
        min_length=1,
    )
    jwt_access_token_expire_minutes: int = Field(
        default=480,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        gt=0,
        le=10080,
    )

    # 127.0.0.1, never "localhost": on Windows that name resolves to ::1 first, and
    # a WSL or Docker port forward on the same port answers there. Pointing at the
    # wrong Ollama makes every review fail, and a failed review is BLOCKED content.
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL"
    )

    ollama_security_model: str = Field(
        default="gemma3:4b",
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

    ollama_generation_model: str = Field(
        default="gemma3:4b",
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
        default=50_000, alias="OLLAMA_GENERATION_MAX_DOCUMENT_CHARS", gt=0
    )
    ollama_vision_model: str = Field(default="gemma3:4b", alias="OLLAMA_VISION_MODEL")
    ollama_vision_timeout_seconds: int = Field(default=180, alias="OLLAMA_VISION_TIMEOUT_SECONDS", gt=0)
    ollama_vision_context_tokens: int = Field(default=8192, alias="OLLAMA_VISION_CONTEXT_TOKENS", gt=0)
    ollama_vision_max_output_tokens: int = Field(default=1200, alias="OLLAMA_VISION_MAX_OUTPUT_TOKENS", gt=0)
    max_document_size_mb: int = Field(default=10, alias="MAX_DOCUMENT_SIZE_MB", gt=0)
    document_storage_backend: str = Field(default="cloudinary", alias="DOCUMENT_STORAGE_BACKEND")
    document_storage_root: Path = Field(default=PROJECT_ROOT / "storage" / "documents", alias="DOCUMENT_STORAGE_DIR")
    cloudinary_cloud_name: str = Field(default="", alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", alias="CLOUDINARY_API_SECRET")
    prompt_max_length: int = Field(default=8000, alias="PROMPT_MAX_LENGTH", gt=0)
    prompt_min_length: int = Field(default=3, alias="PROMPT_MIN_LENGTH", gt=0)

    @field_validator("jwt_secret_key")
    @classmethod
    def reject_development_secret_in_production(cls, value: str, info) -> str:
        environment = str(info.data.get("environment", "development")).lower()
        if environment in {"production", "prod"} and value == "claude-local-development-key-change-before-deploy-2026":
            raise ValueError("JWT_SECRET_KEY must be configured for production")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origin.split(",")
            if origin.strip()
        ]

    @property
    def max_document_size_bytes(self) -> int:
        return self.max_document_size_mb * 1024 * 1024

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
