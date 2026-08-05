from app.iam.application.internal.tokens.jwt_access_token_service import (
    JwtAccessTokenService,
)
from app.iam.domain.model.queries.validate_access_token_query import (
    ValidateAccessTokenQuery,
)
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser
from app.iam.domain.services.authentication_query_service import (
    AuthenticationQueryService,
)


class AuthenticationQueryServiceImpl(AuthenticationQueryService):
    def __init__(self, access_token_service: JwtAccessTokenService) -> None:
        self._access_token_service = access_token_service

    async def handle_validate_access_token(
        self, query: ValidateAccessTokenQuery
    ) -> AuthenticatedUser:
        return self._access_token_service.validate(query.access_token)
