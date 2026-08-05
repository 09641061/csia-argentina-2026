from hmac import compare_digest

from app.iam.application.internal.credentials.configured_credentials import (
    CONFIGURED_PASSWORD,
    CONFIGURED_USERNAME,
)
from app.iam.application.internal.tokens.signed_access_token_service import (
    SignedAccessTokenService,
)
from app.iam.domain.exceptions import InvalidCredentialsError
from app.iam.domain.model.commands.authenticate_user_command import AuthenticateUserCommand
from app.iam.domain.model.events.user_authenticated_event import UserAuthenticatedEvent
from app.iam.domain.model.valueobjects.access_token import AccessToken
from app.iam.domain.services.authentication_command_service import AuthenticationCommandService


class AuthenticationCommandServiceImpl(AuthenticationCommandService):
    def __init__(self, access_token_service: SignedAccessTokenService) -> None:
        self._access_token_service = access_token_service
        self.published_events: list[object] = []

    async def handle_authenticate_user(self, command: AuthenticateUserCommand) -> AccessToken:
        username_matches = compare_digest(command.username.strip(), CONFIGURED_USERNAME)
        password_matches = compare_digest(command.password, CONFIGURED_PASSWORD)
        if not username_matches or not password_matches:
            raise InvalidCredentialsError("Invalid username or password")
        token = self._access_token_service.issue(CONFIGURED_USERNAME)
        self.published_events.append(UserAuthenticatedEvent(username=CONFIGURED_USERNAME))
        return token
