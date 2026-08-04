from typing import Protocol

from app.analysis.domain.model.commands.analyze_document_command import AnalyzeDocumentCommand
from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis


class AnalysisCommandService(Protocol):
    async def handle_analyze_document(self, command: AnalyzeDocumentCommand) -> DocumentAnalysis:
        ...

