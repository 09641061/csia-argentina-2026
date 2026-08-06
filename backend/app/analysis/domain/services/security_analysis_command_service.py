from typing import Protocol

from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.commands.analyze_prompt_command import (
    AnalyzePromptCommand,
)
from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis


class SecurityAnalysisCommandService(Protocol):
    async def handle_analyze_prompt(self, command: AnalyzePromptCommand) -> SecurityAnalysis: ...

    async def handle_analyze_document(
        self,
        command: AnalyzeDocumentCommand,
    ) -> SecurityAnalysis: ...
