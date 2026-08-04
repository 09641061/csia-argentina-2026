from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Iterable

from app.analysis.application.internal.outboundservices.document_content_downloader import DocumentContentDownloader
from app.analysis.application.internal.outboundservices.document_source_service import DocumentSourceService
from app.analysis.application.internal.outboundservices.document_text_extractor import DocumentTextExtractor
from app.analysis.application.internal.outboundservices.ollama_analysis_client import (
    OllamaAnalysisClient,
    OllamaAnalysisInterpretation,
)
from app.analysis.domain.exceptions import DocumentSourceNotFoundError
from app.analysis.domain.model.events.document_analysis_completed_event import DocumentAnalysisCompletedEvent
from app.analysis.domain.model.commands.analyze_document_command import AnalyzeDocumentCommand
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis
from app.analysis.domain.model.valueobjects.analysis_finding_severity import AnalysisFindingSeverity
from app.analysis.domain.model.valueobjects.analysis_finding_type import AnalysisFindingType
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.repositories.document_analysis_repository import DocumentAnalysisRepository
from app.analysis.domain.services.analysis_command_service import AnalysisCommandService


class DocumentAnalysisCommandServiceImpl(AnalysisCommandService):
    def __init__(
        self,
        analysis_repository: DocumentAnalysisRepository,
        document_source_service: DocumentSourceService,
        document_content_downloader: DocumentContentDownloader,
        document_text_extractor: DocumentTextExtractor,
        ollama_analysis_client: OllamaAnalysisClient,
        ollama_model_name: str,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._document_source_service = document_source_service
        self._document_content_downloader = document_content_downloader
        self._document_text_extractor = document_text_extractor
        self._ollama_analysis_client = ollama_analysis_client
        self._ollama_model_name = ollama_model_name
        self.published_events: list[object] = []

    async def handle_analyze_document(self, command: AnalyzeDocumentCommand) -> DocumentAnalysis:
        source = await self._document_source_service.get_document_reference(command.document_id)
        if source is None:
            raise DocumentSourceNotFoundError("Document not found")

        content = await self._document_content_downloader.download(source.document_url)
        extracted_text = self._document_text_extractor.extract_text(
            content,
            source.mime_type,
            source.original_filename,
        )
        findings = self._detect_sensitive_information(extracted_text)
        interpretation = await self._ollama_analysis_client.analyze(
            source=source,
            extracted_text=extracted_text,
            findings=findings,
        )
        risk_level = self._combine_risk_levels(findings, interpretation)
        explanation = self._build_explanation(findings, interpretation)

        analysis = DocumentAnalysis.create(
            document_id=source.document_id,
            source_filename=source.original_filename,
            source_mime_type=source.mime_type,
            source_document_url=source.document_url,
            risk_level=risk_level,
            explanation=explanation,
            model_name=self._ollama_model_name,
            findings=findings,
        )

        saved_analysis = await self._analysis_repository.save(analysis)
        self.published_events.append(
            DocumentAnalysisCompletedEvent(
                analysis_id=saved_analysis.id or 0,
                document_id=saved_analysis.document_id,
                risk_level=saved_analysis.risk_level,
            )
        )
        return saved_analysis

    def _detect_sensitive_information(self, extracted_text: str) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        findings.extend(self._detect_email_addresses(extracted_text))
        findings.extend(self._detect_passwords(extracted_text))
        findings.extend(self._detect_api_keys(extracted_text))
        findings.extend(self._detect_credit_cards(extracted_text))
        findings.extend(self._detect_private_keys(extracted_text))
        return findings

    def _detect_email_addresses(self, text: str) -> list[AnalysisFinding]:
        matches = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))
        return [
            AnalysisFinding(
                finding_type=AnalysisFindingType.EMAIL,
                severity=AnalysisFindingSeverity.LOW,
                title="Email address detected",
                description="The document contains an email address.",
                evidence=match,
            )
            for match in matches
        ]

    def _detect_passwords(self, text: str) -> list[AnalysisFinding]:
        patterns = [
            r"(?i)\bpassword\s*[:=]\s*([^\s,;]+)",
            r"(?i)\bpasswd\s*[:=]\s*([^\s,;]+)",
            r"(?i)\bcontrase[ñn]a\s*[:=]\s*([^\s,;]+)",
        ]
        findings: list[AnalysisFinding] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                evidence = match.group(0)
                findings.append(
                    AnalysisFinding(
                        finding_type=AnalysisFindingType.PASSWORD,
                        severity=AnalysisFindingSeverity.HIGH,
                        title="Password-like secret detected",
                        description="The document appears to contain a password or password-like secret.",
                        evidence=evidence,
                    )
                )
        return findings

    def _detect_api_keys(self, text: str) -> list[AnalysisFinding]:
        patterns = [
            r"(?i)\b(api[_-]?key|secret|token)\b\s*[:=]\s*([A-Za-z0-9_\-./+=]{8,})",
            r"sk-[A-Za-z0-9]{16,}",
            r"AKIA[0-9A-Z]{16}",
        ]
        findings: list[AnalysisFinding] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                evidence = match.group(0)
                findings.append(
                    AnalysisFinding(
                        finding_type=AnalysisFindingType.API_KEY,
                        severity=AnalysisFindingSeverity.HIGH,
                        title="API key or token detected",
                        description="The document appears to contain an API key, secret or token.",
                        evidence=evidence,
                    )
                )
        return findings

    def _detect_credit_cards(self, text: str) -> list[AnalysisFinding]:
        candidates = re.findall(r"\b(?:\d[ -]*?){13,19}\b", text)
        findings: list[AnalysisFinding] = []
        for candidate in candidates:
            digits = re.sub(r"\D", "", candidate)
            if 13 <= len(digits) <= 19 and self._passes_luhn(digits):
                findings.append(
                    AnalysisFinding(
                        finding_type=AnalysisFindingType.CREDIT_CARD,
                        severity=AnalysisFindingSeverity.CRITICAL,
                        title="Credit card number detected",
                        description="The document appears to contain a payment card number.",
                        evidence=candidate,
                    )
                )
        return findings

    def _detect_private_keys(self, text: str) -> list[AnalysisFinding]:
        markers = [
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN RSA PRIVATE KEY-----",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
        ]
        findings: list[AnalysisFinding] = []
        for marker in markers:
            if marker in text:
                findings.append(
                    AnalysisFinding(
                        finding_type=AnalysisFindingType.PRIVATE_KEY,
                        severity=AnalysisFindingSeverity.CRITICAL,
                        title="Private key material detected",
                        description="The document contains private key material.",
                        evidence=marker,
                    )
                )
        return findings

    def _passes_luhn(self, digits: str) -> bool:
        total = 0
        reverse_digits = digits[::-1]
        for index, char in enumerate(reverse_digits):
            digit = int(char)
            if index % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        return total % 10 == 0

    def _combine_risk_levels(
        self,
        findings: Iterable[AnalysisFinding],
        interpretation: OllamaAnalysisInterpretation,
    ) -> AnalysisRiskLevel:
        severity_order = {
            AnalysisRiskLevel.LOW: 0,
            AnalysisRiskLevel.MEDIUM: 1,
            AnalysisRiskLevel.HIGH: 2,
            AnalysisRiskLevel.CRITICAL: 3,
        }
        base_risk = AnalysisRiskLevel.LOW
        for finding in findings:
            if finding.severity == AnalysisFindingSeverity.CRITICAL:
                base_risk = AnalysisRiskLevel.CRITICAL
                break
            if finding.severity == AnalysisFindingSeverity.HIGH:
                base_risk = max(base_risk, AnalysisRiskLevel.HIGH, key=severity_order.get)
            elif finding.severity == AnalysisFindingSeverity.MEDIUM:
                base_risk = max(base_risk, AnalysisRiskLevel.MEDIUM, key=severity_order.get)

        return max(base_risk, interpretation.risk_level, key=severity_order.get)

    def _build_explanation(
        self,
        findings: list[AnalysisFinding],
        interpretation: OllamaAnalysisInterpretation,
    ) -> str:
        if findings:
            return f"{interpretation.summary} Se detectaron {len(findings)} hallazgos relevantes."
        return interpretation.summary or interpretation.rationale
