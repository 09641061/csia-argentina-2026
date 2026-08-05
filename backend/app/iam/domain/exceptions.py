class InvalidCredentialsError(ValueError):
    """The supplied username or password is not valid."""


class InvalidAccessTokenError(ValueError):
    """The supplied access token is invalid or expired."""
