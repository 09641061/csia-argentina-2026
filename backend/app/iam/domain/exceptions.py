class InvalidCredentialsError(ValueError):
    """The supplied username or password is not valid."""


class InvalidAccessTokenError(ValueError):
    """The supplied access token is invalid or expired."""


class UsernameAlreadyRegisteredError(ValueError):
    """The requested username is already registered."""


class WeakPasswordError(ValueError):
    """The supplied password does not meet the local account policy."""
