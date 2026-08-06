from typing import Protocol


class DecisionContextValidationError(ValueError):
    """The submitted chat content is not valid for the secure-query capability."""


class DecisionContextFacade(Protocol):
    async def execute_authorized_query(
        self,
        *,
        prompt: str | None,
        requested_by: str,
    ) -> dict[str, object | None]: ...
