from app.decision.domain.model.entities.secure_interaction import SecureInteraction
from app.decision.domain.model.queries.get_secure_interaction_by_id_query import (
    GetSecureInteractionByIdQuery,
)
from app.decision.domain.model.queries.list_secure_interactions_query import (
    ListSecureInteractionsQuery,
)
from app.decision.domain.repositories.secure_interaction_repository import (
    SecureInteractionRepository,
)
from app.decision.domain.services.secure_interaction_query_service import (
    SecureInteractionQueryService,
)


class SecureInteractionQueryServiceImpl(SecureInteractionQueryService):
    def __init__(self, interaction_repository: SecureInteractionRepository) -> None:
        self._interaction_repository = interaction_repository

    async def handle_get_secure_interaction_by_id(
        self,
        query: GetSecureInteractionByIdQuery,
    ) -> SecureInteraction | None:
        return await self._interaction_repository.find_by_id(query.interaction_id)

    async def handle_list_secure_interactions(
        self,
        query: ListSecureInteractionsQuery,
    ) -> tuple[list[SecureInteraction], int]:
        return await self._interaction_repository.list(query.page, query.page_size)
