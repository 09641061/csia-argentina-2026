from typing import Protocol

from app.decision.domain.model.entities.secure_interaction import SecureInteraction


class SecureInteractionRepository(Protocol):
    async def save(self, interaction: SecureInteraction) -> SecureInteraction: ...

    async def find_by_id(self, interaction_id: int) -> SecureInteraction | None: ...

    async def list(self, page: int, page_size: int) -> tuple[list[SecureInteraction], int]: ...
