from app.iam.application.internal.security.password_hashing_service import (
    PasswordHashingService,
)
from app.iam.application.internal.tokens.jwt_access_token_service import (
    JwtAccessTokenService,
)
from app.iam.domain.exceptions import (
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
)
from app.iam.domain.model.commands.authenticate_user_command import (
    AuthenticateUserCommand,
)
from app.iam.domain.model.commands.register_user_command import RegisterUserCommand
from app.iam.domain.model.entities.user_account import UserAccount
from app.iam.domain.model.events.user_authenticated_event import UserAuthenticatedEvent
from app.iam.domain.model.valueobjects.access_token import AccessToken
from app.iam.domain.model.valueobjects.username import Username
from app.iam.domain.repositories.user_account_repository import UserAccountRepository
from app.iam.domain.services.authentication_command_service import (
    AuthenticationCommandService,
)


class AuthenticationCommandServiceImpl(AuthenticationCommandService):
    def __init__(
        self,
        user_repository: UserAccountRepository,
        access_token_service: JwtAccessTokenService,
        password_hashing_service: PasswordHashingService,
    ) -> None:
        self._user_repository = user_repository
        self._access_token_service = access_token_service
        self._password_hashing_service = password_hashing_service
        self.published_events: list[object] = []

    async def handle_authenticate_user(
        self, command: AuthenticateUserCommand
    ) -> AccessToken:
        username = Username(command.username)
        account = await self._user_repository.find_by_username(username)
        if account is None:
            await asyncio.to_thread(self._password_hashing_service.verify_dummy, command.password)
            raise InvalidCredentialsError("Invalid username or password")
        if not await asyncio.to_thread(
            self._password_hashing_service.verify, command.password, account.password_hash
        ):
            raise InvalidCredentialsError("Invalid username or password")
        token = self._access_token_service.issue(account.username.value)
        self.published_events.append(
            UserAuthenticatedEvent(username=account.username.value)
        )
        return token

    async def handle_register_user(self, command: RegisterUserCommand) -> AccessToken:
        username = Username(command.username)
        if await self._user_repository.find_by_username(username) is not None:
            raise UsernameAlreadyRegisteredError("Username is already registered")
        account = await self._user_repository.save(
            UserAccount(
                id=None,
                username=username,
                password_hash=await asyncio.to_thread(
                    self._password_hashing_service.hash, command.password
                ),
            )
        )
        token = self._access_token_service.issue(account.username.value)
        self.published_events.append(
            UserAuthenticatedEvent(username=account.username.value)
        )
        return token
import asyncio
