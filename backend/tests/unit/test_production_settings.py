import pytest
from pydantic import ValidationError

from app.core.settings import Settings


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", _env_file=None)


def test_production_accepts_an_explicit_jwt_secret() -> None:
    settings = Settings(
        environment="production",
        jwt_secret_key="a-unique-production-secret-with-at-least-32-characters",
        _env_file=None,
    )

    assert settings.environment == "production"
