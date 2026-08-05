from typing import Protocol

from app.decision.domain.model.entities.secure_interaction import SecureInteraction
from app.decision.domain.model.queries.get_secure_interaction_by_id_query import (
    GetSecureInteractionByIdQuery,
)
from app.decision.domain.model.queries.list_secure_interactions_query import (
    ListSecureInteractionsQuery,
)


class SecureInteractionQueryService(Protocol):
    async def handle_get_secure_interaction_by_id(
        self,
        query: GetSecureInteractionByIdQuery,
    ) -> SecureInteraction | None: ...

    async def handle_list_secure_interactions(
        self,
        query: ListSecureInteractionsQuery,
    ) -> tuple[list[SecureInteraction], int]: ...
