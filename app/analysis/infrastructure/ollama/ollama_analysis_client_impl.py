from __future__ import annotations

import asyncio
import json
import ssl
from urllib.request import Request, urlopen

import certifi

from app.analysis.application.internal.outboundservices.ollama_analysis_client import (
    OllamaAnalysisClient,
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.source_document_reference import SourceDocumentReference


class OllamaAnalysisClientImpl(OllamaAnalysisClient):
    def __init__(self, base_url: str, model_name: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name

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
        prompt = self._build_prompt(source, extracted_text, findings)
        request_payload = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        body = json.dumps(request_payload).encode("utf-8")
        request = Request(
            url=f"{self._base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=60, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
        raw_response = payload.get("response", "{}")
        try:
            response_data = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
        except json.JSONDecodeError:
            response_data = {}

        return OllamaAnalysisInterpretation(
            risk_level=self._parse_risk_level(str(response_data.get("risk_level", "low"))),
            summary=str(response_data.get("summary", "")).strip(),
            rationale=str(response_data.get("rationale", "")).strip(),
        )

    def _build_prompt(
        self,
        source: SourceDocumentReference,
        extracted_text: str,
        findings: list[AnalysisFinding],
    ) -> str:
        findings_text = "\n".join(
            f"- [{finding.severity.value}] {finding.title}: {finding.evidence}"
            for finding in findings
        ) or "No rule-based findings."
        excerpt = extracted_text[:6000]
        return (
            "You are a document risk analysis assistant.\n"
            "Return ONLY valid JSON with keys: risk_level, summary, rationale.\n"
            "Allowed risk_level values: low, medium, high, critical.\n\n"
            f"Document: {source.original_filename}\n"
            f"MIME type: {source.mime_type}\n\n"
            f"Rule-based findings:\n{findings_text}\n\n"
            f"Extracted text:\n{excerpt}\n"
        )

    def _parse_risk_level(self, value: str) -> AnalysisRiskLevel:
        normalized = value.strip().lower()
        if normalized in {level.value for level in AnalysisRiskLevel}:
            return AnalysisRiskLevel(normalized)
        return AnalysisRiskLevel.LOW

