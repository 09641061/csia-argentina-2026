from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.iam.application.internal.commandservices.authentication_command_service_impl import (
    AuthenticationCommandServiceImpl,
)
from app.iam.application.internal.queryservices.authentication_query_service_impl import (
    AuthenticationQueryServiceImpl,
)
from app.iam.application.internal.tokens.signed_access_token_service import SignedAccessTokenService
from app.iam.domain.exceptions import InvalidAccessTokenError, InvalidCredentialsError
from app.iam.domain.model.commands.authenticate_user_command import AuthenticateUserCommand
from app.iam.domain.model.queries.validate_access_token_query import ValidateAccessTokenQuery
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.interfaces.rest.resources.login_request import LoginRequest
from app.iam.interfaces.rest.resources.login_response import LoginResponse

router = APIRouter(prefix="/api/v1/auth", tags=["IAM"])
bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_token_service() -> SignedAccessTokenService:
    return SignedAccessTokenService()


def get_authentication_command_service() -> AuthenticationCommandServiceImpl:
    return AuthenticationCommandServiceImpl(get_token_service())


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
    description="Validates the configured username and password and returns a signed bearer token.",
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
            AuthenticateUserCommand(username=request.username, password=request.password)
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return LoginResponse(
        access_token=token.value,
        token_type="bearer",
        expires_at=token.expires_at,
    )
