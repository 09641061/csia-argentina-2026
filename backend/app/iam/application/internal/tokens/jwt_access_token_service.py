from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from app.iam.domain.exceptions import InvalidAccessTokenError
from app.iam.domain.model.valueobjects.access_token import AccessToken
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.domain.model.valueobjects.username import Username

_ALGORITHM = "HS256"


class JwtAccessTokenService:
    def __init__(
        self,
        *,
        secret_key: str,
        issuer: str,
        audience: str,
        lifetime_minutes: int,
    ) -> None:
        if len(secret_key) < 32:
            raise ValueError("JWT secret key must contain at least 32 characters")
        self._secret_key = secret_key
        self._issuer = issuer
        self._audience = audience
        self._lifetime = timedelta(minutes=lifetime_minutes)

    def issue(self, username: str) -> AccessToken:
        now = datetime.now(UTC)
        expires_at = now + self._lifetime
        token = jwt.encode(
            {
                "sub": Username(username).value,
                "iat": now,
                "exp": expires_at,
                "iss": self._issuer,
                "aud": self._audience,
                "jti": uuid4().hex,
                "type": "access",
            },
            self._secret_key,
            algorithm=_ALGORITHM,
        )
        return AccessToken(value=token, expires_at=expires_at)

    def validate(self, token: str) -> AuthenticatedUser:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[_ALGORITHM],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["sub", "iat", "exp", "iss", "aud", "jti", "type"]},
            )
            if payload.get("type") != "access":
                raise InvalidAccessTokenError("Invalid access token")
            username = Username(str(payload["sub"]))
        except InvalidAccessTokenError:
            raise
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
            raise InvalidAccessTokenError("Invalid or expired access token") from error
        return AuthenticatedUser(username=username)
