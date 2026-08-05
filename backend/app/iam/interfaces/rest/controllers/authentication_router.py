from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.settings import get_settings
from app.iam.application.internal.commandservices.authentication_command_service_impl import (
    AuthenticationCommandServiceImpl,
)
from app.iam.application.internal.queryservices.authentication_query_service_impl import (
    AuthenticationQueryServiceImpl,
)
from app.iam.application.internal.security.password_hashing_service import (
    PasswordHashingService,
)
from app.iam.application.internal.tokens.jwt_access_token_service import (
    JwtAccessTokenService,
)
from app.iam.domain.exceptions import (
    InvalidAccessTokenError,
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
    WeakPasswordError,
)
from app.iam.domain.model.commands.authenticate_user_command import (
    AuthenticateUserCommand,
)
from app.iam.domain.model.commands.register_user_command import RegisterUserCommand
from app.iam.domain.model.queries.validate_access_token_query import (
    ValidateAccessTokenQuery,
)
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.domain.model.valueobjects.username import Username
from app.iam.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_user_account_repository import (
    SqlAlchemyUserAccountRepository,
)
from app.iam.interfaces.rest.resources.authenticated_user_resource import (
    AuthenticatedUserResource,
)
from app.iam.interfaces.rest.resources.login_request import LoginRequest
from app.iam.interfaces.rest.resources.login_response import LoginResponse
from app.iam.interfaces.rest.resources.register_request import RegisterRequest

router = APIRouter(prefix="/api/v1/auth", tags=["IAM"])
bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_token_service() -> JwtAccessTokenService:
    settings = get_settings()
    return JwtAccessTokenService(
        secret_key=settings.jwt_secret_key,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        lifetime_minutes=settings.jwt_access_token_expire_minutes,
    )


@lru_cache(maxsize=1)
def get_password_hashing_service() -> PasswordHashingService:
    return PasswordHashingService()


def get_authentication_command_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthenticationCommandServiceImpl:
    return AuthenticationCommandServiceImpl(
        user_repository=SqlAlchemyUserAccountRepository(session),
        access_token_service=get_token_service(),
        password_hashing_service=get_password_hashing_service(),
    )


def get_authentication_query_service() -> AuthenticationQueryServiceImpl:
    return AuthenticationQueryServiceImpl(get_token_service())


async def require_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    query_service: Annotated[
        AuthenticationQueryServiceImpl, Depends(get_authentication_query_service)
    ],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await query_service.handle_validate_access_token(
            ValidateAccessTokenQuery(access_token=credentials.credentials)
        )
    except (InvalidAccessTokenError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
    description="Validates a registered local account and returns a signed bearer token.",
    responses={
        200: {"description": "Credentials accepted"},
        401: {"description": "Invalid username or password"},
        422: {"description": "Malformed login request"},
    },
)
async def login(
    request: LoginRequest,
    command_service: Annotated[
        AuthenticationCommandServiceImpl, Depends(get_authentication_command_service)
    ],
) -> LoginResponse:
    try:
        token = await command_service.handle_authenticate_user(
            AuthenticateUserCommand(
                username=request.username, password=request.password
            )
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return LoginResponse(
        access_token=token.value,
        token_type="bearer",
        expires_at=token.expires_at,
        username=Username(request.username).value,
    )


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a local user",
    description=(
        "Creates a local account with an Argon2 password hash and returns a signed JWT access "
        "token. Plaintext passwords are never stored."
    ),
    responses={
        201: {"description": "Account created and authenticated"},
        409: {"description": "Username already registered"},
        422: {"description": "Username or password does not meet the account policy"},
    },
)
async def register(
    request: RegisterRequest,
    command_service: Annotated[
        AuthenticationCommandServiceImpl, Depends(get_authentication_command_service)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LoginResponse:
    try:
        token = await command_service.handle_register_user(
            RegisterUserCommand(username=request.username, password=request.password)
        )
        await session.commit()
    except (UsernameAlreadyRegisteredError, IntegrityError) as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está registrado.",
        ) from error
    except WeakPasswordError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return LoginResponse(
        access_token=token.value,
        token_type="bearer",
        expires_at=token.expires_at,
        username=Username(request.username).value,
    )


@router.get(
    "/me",
    response_model=AuthenticatedUserResource,
    summary="Get the authenticated user",
    description="Validates the JWT Bearer token and returns its local account identity.",
    responses={401: {"description": "Invalid or expired access token"}},
)
async def get_authenticated_user(
    user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> AuthenticatedUserResource:
    return AuthenticatedUserResource(username=user.identity)
