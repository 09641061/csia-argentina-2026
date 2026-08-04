from __future__ import annotations

import asyncio
import json
import ssl
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

from app.analysis.application.internal.outboundservices.ollama_analysis_client import (
    OllamaAnalysisClient,
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.exceptions import AnalysisModelUnavailableError
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.analysis_finding_severity import AnalysisFindingSeverity
from app.analysis.domain.model.valueobjects.source_document_reference import SourceDocumentReference

MAX_EXCERPT_CHARS = 6000
MAX_PROMPT_FINDINGS = 20

SEVERITY_ORDER = {
    AnalysisFindingSeverity.CRITICAL: 0,
    AnalysisFindingSeverity.HIGH: 1,
    AnalysisFindingSeverity.MEDIUM: 2,
    AnalysisFindingSeverity.LOW: 3,
}


class OllamaAnalysisClientImpl(OllamaAnalysisClient):
    def __init__(
        self,
        base_url: str,
        model_name: str,
        request_timeout_seconds: int,
        context_tokens: int,
        max_output_tokens: int,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._request_timeout_seconds = request_timeout_seconds
        self._context_tokens = context_tokens
        self._max_output_tokens = max_output_tokens
        self._system_prompt = self._load_system_prompt()

    async def analyze(
        self,
        *,
        source: SourceDocumentReference,
        extracted_text: str,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation:
        payload = await asyncio.to_thread(
            self._generate,
            source,
            extracted_text,
            findings,
        )
        return payload

    def _generate(
        self,
        source: SourceDocumentReference,
        extracted_text: str,
        findings: list[AnalysisFinding],
    ) -> OllamaAnalysisInterpretation:
        prompt = self._build_user_prompt(source, extracted_text, findings)
        request_payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "num_ctx": self._context_tokens,
                "num_predict": self._max_output_tokens,
            },
        }
        body = json.dumps(request_payload).encode("utf-8")
        request = Request(
            url=f"{self._base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        context = ssl.create_default_context(cafile=certifi.where())
        try:
            with urlopen(request, timeout=self._request_timeout_seconds, context=context) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as error:
            raise AnalysisModelUnavailableError(
                f"Model {self._model_name} did not answer within {self._request_timeout_seconds} seconds"
            ) from error
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise AnalysisModelUnavailableError(
                f"Model {self._model_name} failed with HTTP {error.code}: {detail}"
            ) from error
        except URLError as error:
            raise AnalysisModelUnavailableError(
                f"Unable to reach Ollama at {self._base_url}: {error.reason}"
            ) from error
        raw_response = payload.get("message", {}).get("content", "{}")
        try:
            response_data = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
        except json.JSONDecodeError:
            response_data = {}

        return OllamaAnalysisInterpretation(
            risk_level=self._parse_risk_level(str(response_data.get("risk_level", "low"))),
            summary=str(response_data.get("summary", "")).strip(),
            rationale=str(response_data.get("rationale", "")).strip(),
        )

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).resolve().parents[3] / "shared" / "prompts" / "document_analysis_system_prompt.md"
        return prompt_path.read_text(encoding="utf-8").strip()

    def _build_user_prompt(
        self,
        source: SourceDocumentReference,
        extracted_text: str,
        findings: list[AnalysisFinding],
    ) -> str:
        findings_text = self._build_findings_text(findings)
        excerpt = extracted_text[:MAX_EXCERPT_CHARS]
        return (
            "You are a document risk analysis assistant.\n"
            "Return ONLY valid JSON with keys: risk_level, summary, rationale.\n"
            "Allowed risk_level values: low, medium, high, critical.\n\n"
            f"Document: {source.original_filename}\n"
            f"MIME type: {source.mime_type}\n\n"
            f"Rule-based findings:\n{findings_text}\n\n"
            f"Extracted text:\n{excerpt}\n"
        )

    def _build_findings_text(self, findings: list[AnalysisFinding]) -> str:
        """
        Renders the most severe findings only.

        The number of rule-based findings is unbounded, and an oversized prompt
        overflows the model context: the instructions are dropped and the model
        echoes the document back instead of analyzing it.
        """

        if not findings:
            return "No rule-based findings."

        ranked = sorted(findings, key=lambda finding: SEVERITY_ORDER[finding.severity])
        listed = ranked[:MAX_PROMPT_FINDINGS]

        lines = [
            f"- [{finding.severity.value}] {finding.title}: {finding.evidence}"
            for finding in listed
        ]

        omitted = len(ranked) - len(listed)
        if omitted > 0:
            lines.append(f"- ... and {omitted} more finding(s) of equal or lower severity.")

        return "\n".join(lines)

    def _parse_risk_level(self, value: str) -> AnalysisRiskLevel:
        normalized = value.strip().lower()
        if normalized in {level.value for level in AnalysisRiskLevel}:
            return AnalysisRiskLevel(normalized)
        return AnalysisRiskLevel.LOW
