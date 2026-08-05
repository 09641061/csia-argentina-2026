from __future__ import annotations

from dataclasses import replace

from app.analysis.application.internal.services.json_path import append_json_path
from app.analysis.application.internal.services.prompt_sensitive_data_detection_service import (
    PromptSensitiveDataDetectionService,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.json_types import JsonContainer, JsonValue


class DocumentFreeTextSensitiveDataDetectionService:
    """Applies the bilingual prompt rules to every text leaf extracted from a file."""

    def __init__(
        self,
        prompt_detector: PromptSensitiveDataDetectionService | None = None,
    ) -> None:
        self._prompt_detector = prompt_detector or PromptSensitiveDataDetectionService()

    def scan(self, content: JsonContainer) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        self._walk(content, "$", findings)
        return [
            replace(finding, finding_id=f"f{index}")
            for index, finding in enumerate(findings, start=1)
        ]

    def _walk(
        self,
        value: JsonValue,
        path: str,
        findings: list[AnalysisFinding],
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                self._walk(child, append_json_path(path, key), findings)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                self._walk(child, append_json_path(path, index), findings)
            return
        if not isinstance(value, str) or not value.strip():
            return
        findings.extend(
            replace(finding, json_path=path)
            for finding in self._prompt_detector.scan(value)
        )
