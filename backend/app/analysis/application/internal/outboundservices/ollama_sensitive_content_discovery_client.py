from typing import Protocol

from app.analysis.domain.model.valueobjects.json_types import JsonContainer
from app.analysis.domain.model.valueobjects.sensitive_content_discovery import (
    SensitiveContentDiscovery,
)


class OllamaSensitiveContentDiscoveryClient(Protocol):
    """Mandatory local-AI inspection of unmasked extracted document content."""

    @property
    def model_name(self) -> str: ...

    async def inspect(
        self,
        *,
        content: JsonContainer,
        reference_label: str,
    ) -> SensitiveContentDiscovery: ...
