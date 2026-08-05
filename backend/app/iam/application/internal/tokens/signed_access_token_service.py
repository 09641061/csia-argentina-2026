import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta

from app.iam.domain.exceptions import InvalidAccessTokenError
from app.iam.domain.model.valueobjects.access_token import AccessToken
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.domain.model.valueobjects.username import Username

_TOKEN_SECRET = secrets.token_bytes(32)
_TOKEN_LIFETIME = timedelta(hours=8)


class SignedAccessTokenService:
    def issue(self, username: str) -> AccessToken:
        expires_at = datetime.now(UTC) + _TOKEN_LIFETIME
        payload = json.dumps(
            {"sub": username, "exp": int(expires_at.timestamp())},
            separators=(",", ":"),
        ).encode()
        encoded_payload = base64.urlsafe_b64encode(payload).decode().rstrip("=")
        signature = hmac.new(_TOKEN_SECRET, encoded_payload.encode(), hashlib.sha256).hexdigest()
        return AccessToken(value=f"{encoded_payload}.{signature}", expires_at=expires_at)

    def validate(self, token: str) -> AuthenticatedUser:
        try:
            encoded_payload, supplied_signature = token.split(".", maxsplit=1)
            expected_signature = hmac.new(
                _TOKEN_SECRET, encoded_payload.encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(supplied_signature, expected_signature):
                raise InvalidAccessTokenError("Invalid access token")
            padding = "=" * (-len(encoded_payload) % 4)
            payload = json.loads(base64.urlsafe_b64decode(encoded_payload + padding))
            username = str(payload["sub"])
            expires_at = datetime.fromtimestamp(int(payload["exp"]), UTC)
        except InvalidAccessTokenError:
            raise
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise InvalidAccessTokenError("Invalid access token") from error
        if expires_at <= datetime.now(UTC):
            raise InvalidAccessTokenError("Access token has expired")
        return AuthenticatedUser(username=Username(username))
