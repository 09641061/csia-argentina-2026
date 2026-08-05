import jwt
import pytest

from app.iam.application.internal.tokens.jwt_access_token_service import (
    JwtAccessTokenService,
)
from app.iam.domain.exceptions import InvalidAccessTokenError

SECRET = "sentinel-test-secret-with-at-least-thirty-two-characters"


def service(secret_key: str = SECRET) -> JwtAccessTokenService:
    return JwtAccessTokenService(
        secret_key=secret_key,
        issuer="sentinel-test",
        audience="sentinel-web-test",
        lifetime_minutes=30,
    )


def test_issued_token_is_a_standard_jwt_and_survives_service_recreation() -> None:
    token = service().issue("Sentinel.Demo")

    header = jwt.get_unverified_header(token.value)
    authenticated = service().validate(token.value)

    assert header["alg"] == "HS256"
    assert token.value.count(".") == 2
    assert authenticated.identity == "sentinel.demo"


def test_token_signed_with_another_secret_is_rejected() -> None:
    token = service().issue("sentinel.demo")

    with pytest.raises(InvalidAccessTokenError):
        service("another-sentinel-test-secret-with-thirty-two-characters").validate(
            token.value
        )
