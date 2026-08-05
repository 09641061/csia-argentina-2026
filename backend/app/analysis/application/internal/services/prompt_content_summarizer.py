from __future__ import annotations

import re
from collections import Counter

from app.analysis.application.internal.services.prompt_sensitive_data_detection_service import (
    PromptSensitiveDataDetectionService,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_finding_type import AnalysisFindingType
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.prompt_content_summary import PromptContentSummary
from app.shared.domain.text_masking import mask_free_text

MAX_EXCERPT_CHARACTERS = 400

_SPANISH_MARKERS = re.compile(
    r"(?i)\b(?:el|la|los|las|de|que|para|con|una?|por|como|resumen|consulta|informaci(?:o|ó)n)\b"
)
_PERSONAL_TYPES = {
    AnalysisFindingType.EMAIL,
    AnalysisFindingType.FULL_NAME,
    AnalysisFindingType.PHONE,
    AnalysisFindingType.PERSONAL_ID,
    AnalysisFindingType.PASSPORT,
    AnalysisFindingType.CREDIT_CARD,
    AnalysisFindingType.BANK_ACCOUNT,
}


class PromptContentSummarizer:
    """
    Turns a prompt into a masked structural description.

    The excerpt sent to the security model is masked with the shared free-text
    masker, so no complete credential, email or identifier can travel inside it.
    """

    def __init__(self, detector: PromptSensitiveDataDetectionService | None = None) -> None:
        self._detector = detector or PromptSensitiveDataDetectionService()

    def summarize(self, prompt: str, findings: list[AnalysisFinding]) -> PromptContentSummary:
        normalized = prompt.strip()
        excerpt = self._detector.mask_text(normalized[:MAX_EXCERPT_CHARACTERS])
        finding_counts = Counter(finding.finding_type.value for finding in findings)
        categories = sorted(
            {finding.data_category for finding in findings if finding.data_category}
        )
        subject_count = len(
            {
                finding.evidence
                for finding in findings
                if finding.finding_type in _PERSONAL_TYPES
            }
        )
        return PromptContentSummary(
            character_count=len(normalized),
            word_count=len(normalized.split()),
            line_count=normalized.count("\n") + 1,
            language_hint="es" if _SPANISH_MARKERS.search(normalized) else "unknown",
            masked_excerpt=excerpt,
            finding_counts=tuple(sorted(finding_counts.items())),
            data_categories=tuple(categories),
            estimated_subjects=self._estimate_subjects(subject_count),
            injection_markers=self._detector.injection_markers(normalized),
            truncated=len(normalized) > MAX_EXCERPT_CHARACTERS,
        )

    def _estimate_subjects(self, subject_count: int) -> EstimatedSubjects:
        if subject_count == 0:
            return EstimatedSubjects.ZERO
        if subject_count <= 5:
            return EstimatedSubjects.ONE_TO_FIVE
        if subject_count <= 100:
            return EstimatedSubjects.SIX_TO_ONE_HUNDRED
        return EstimatedSubjects.OVER_ONE_HUNDRED
