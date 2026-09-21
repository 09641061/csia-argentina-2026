from typing import Protocol

from app.iam.domain.model.queries.validate_access_token_query import (
    ValidateAccessTokenQuery,
)
from app.iam.domain.model.valueobjects.authenticated_user import AuthenticatedUser


class AuthenticationQueryService(Protocol):
    async def handle_validate_access_token(
        self, query: ValidateAccessTokenQuery
    ) -> AuthenticatedUser: ...
