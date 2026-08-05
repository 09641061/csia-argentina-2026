from typing import Protocol

from app.decision.domain.model.commands.submit_secure_query_command import (
    SubmitSecureQueryCommand,
)
from app.decision.domain.model.valueobjects.secure_query_result import SecureQueryResult


class SecureQueryCommandService(Protocol):
    async def handle_submit_secure_query(
        self, command: SubmitSecureQueryCommand
    ) -> SecureQueryResult: ...
