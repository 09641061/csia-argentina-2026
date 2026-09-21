from typing import Protocol
from typing import Any


class DecisionContextValidationError(ValueError):
    """The submitted chat content is not valid for the secure-query capability."""


class DecisionContextFacade(Protocol):
    async def execute_authorized_query(
        self,
        *,
        prompt: str | None,
        requested_by: str,
        attachment_payload: dict[str, Any] | list[Any] | None = None,
        attachment_name: str | None = None,
    ) -> dict[str, object | None]: ...
