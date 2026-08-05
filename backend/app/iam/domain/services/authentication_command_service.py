from typing import Protocol

from app.iam.domain.model.commands.authenticate_user_command import (
    AuthenticateUserCommand,
)
from app.iam.domain.model.commands.register_user_command import RegisterUserCommand
from app.iam.domain.model.valueobjects.access_token import AccessToken


class AuthenticationCommandService(Protocol):
    async def handle_authenticate_user(
        self, command: AuthenticateUserCommand
    ) -> AccessToken: ...

    async def handle_register_user(
        self, command: RegisterUserCommand
    ) -> AccessToken: ...
