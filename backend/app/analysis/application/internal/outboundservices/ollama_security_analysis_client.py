from typing import Protocol

from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.ollama_analysis_interpretation import (
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.valueobjects.security_evaluation_context import (
    SecurityEvaluationContext,
)


class OllamaSecurityAnalysisClient(Protocol):
    """
    Use 1 of Ollama: contextual security evaluation.

    Separate from the answer generator on purpose. It has its own system prompt,
    its own strict JSON contract and its own timeout, and it only ever sees
    masked, summarized content.
    """

    async def evaluate(
        self,
        *,
        context: SecurityEvaluationContext,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation: ...
