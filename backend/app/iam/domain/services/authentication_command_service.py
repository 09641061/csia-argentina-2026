from typing import Protocol

from app.iam.domain.model.commands.authenticate_user_command import AuthenticateUserCommand
from app.iam.domain.model.valueobjects.access_token import AccessToken


class AuthenticationCommandService(Protocol):
    async def handle_authenticate_user(self, command: AuthenticateUserCommand) -> AccessToken: ...
