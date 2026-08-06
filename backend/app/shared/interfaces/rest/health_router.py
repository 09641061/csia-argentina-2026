import asyncio
import json
from urllib.request import urlopen

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.core.database import check_database_connection
from app.core.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["Health"])


class HealthResponse(BaseModel):
    """
    Readiness of the dependencies the product cannot work without.

    The frontend uses it to tell a person "the service is not available" instead
    of showing a raw network error.
    """

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="ok when every dependency answered", examples=["ok"])
    database: bool = Field(description="PostgreSQL answered a trivial query")
    security_model_available: bool = Field(
        description="The security evaluation model is installed in the local Ollama"
    )
    discovery_model_available: bool = Field(
        description="The raw sensitive-content discovery model is installed in local Ollama"
    )
    generation_model_available: bool = Field(
        description="The answer generation model is installed in the local Ollama"
    )
    security_model: str = Field(description="Configured security model", examples=["gemma3:4b"])
    discovery_model: str = Field(
        description="Configured sensitive-content discovery model", examples=["gemma3:4b"]
    )
    generation_model: str = Field(
        description="Configured generation model", examples=["gemma3:4b"]
    )


def _installed_models(base_url: str) -> set[str]:
    try:
        with urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - a health probe must never raise
        return set()
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return set()
    return {str(item.get("model", "")) for item in models if isinstance(item, dict)}


def _model_is_installed(model_name: str, installed: set[str]) -> bool:
    if model_name in installed:
        return True
    if ":" not in model_name:
        return f"{model_name}:latest" in installed
    return False


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Readiness of the local dependencies",
    description="Reports whether PostgreSQL and the configured local Ollama models are reachable.",
    responses={200: {"description": "Health report returned"}},
)
async def get_health() -> HealthResponse:
    settings = get_settings()
    database_ok, installed = await asyncio.gather(
        check_database_connection(),
        asyncio.to_thread(_installed_models, settings.ollama_base_url),
    )
    security_ok = _model_is_installed(settings.ollama_security_model, installed)
    discovery_ok = _model_is_installed(settings.ollama_discovery_model, installed)
    generation_ok = _model_is_installed(settings.ollama_generation_model, installed)
    return HealthResponse(
        status=(
            "ok"
            if database_ok and security_ok and discovery_ok and generation_ok
            else "degraded"
        ),
        database=database_ok,
        security_model_available=security_ok,
        discovery_model_available=discovery_ok,
        generation_model_available=generation_ok,
        security_model=settings.ollama_security_model,
        discovery_model=settings.ollama_discovery_model,
        generation_model=settings.ollama_generation_model,
    )
