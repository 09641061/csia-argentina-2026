from __future__ import annotations

import hashlib
import logging
from dataclasses import replace

from app.analysis.application.internal.outboundservices.document_source_service import (
    DocumentSourceService,
)
from app.analysis.application.internal.outboundservices.document_text_extractor import (
    DocumentTextExtractor,
)
from app.analysis.application.internal.outboundservices.ollama_security_analysis_client import (
    OllamaSecurityAnalysisClient,
)
from app.analysis.application.internal.outboundservices.ollama_sensitive_content_discovery_client import (
    OllamaSensitiveContentDiscoveryClient,
)
from app.analysis.application.internal.services.content_sanitization_service import (
    ContentSanitizationService,
)
from app.analysis.application.internal.services.document_free_text_sensitive_data_detection_service import (
    DocumentFreeTextSensitiveDataDetectionService,
)
from app.analysis.application.internal.services.document_structure_summarizer import (
    DocumentStructureSummarizer,
)
from app.analysis.application.internal.services.prompt_content_summarizer import (
    PromptContentSummarizer,
)
from app.analysis.application.internal.services.prompt_sensitive_data_detection_service import (
    PromptSensitiveDataDetectionService,
)
from app.analysis.application.internal.services.risk_calculation_service import (
    RiskCalculationService,
)
from app.analysis.application.internal.services.sensitive_data_detection_service import (
    SensitiveDataDetectionService,
)
from app.analysis.domain.exceptions import (
    AnalysisExecutionError,
    AnalysisModelError,
    AnalysisModelTimeoutError,
    AnalysisModelUnavailableError,
    DocumentContentExtractionError,
    DocumentContentReadError,
    DocumentSourceNotFoundError,
    InvalidPromptError,
)
from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.commands.analyze_prompt_command import (
    AnalyzePromptCommand,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis
from app.analysis.domain.model.events.security_analysis_completed_event import (
    SecurityAnalysisCompletedEvent,
)
from app.analysis.domain.model.events.security_analysis_failed_event import (
    SecurityAnalysisFailedEvent,
)
from app.analysis.domain.model.events.security_analysis_started_event import (
    SecurityAnalysisStartedEvent,
)
from app.analysis.domain.model.valueobjects.analyzed_content_type import (
    AnalyzedContentType,
)
from app.analysis.domain.model.valueobjects.security_evaluation_context import (
    SecurityEvaluationContext,
)
from app.analysis.domain.model.valueobjects.sensitive_content_discovery import (
    SensitiveContentDiscovery,
)
from app.analysis.domain.repositories.security_analysis_repository import (
    SecurityAnalysisRepository,
)
from app.analysis.domain.services.security_analysis_command_service import (
    SecurityAnalysisCommandService,
)
from app.shared.domain.text_masking import mask_free_text

logger = logging.getLogger(__name__)

MASKED_PREVIEW_MAX_CHARACTERS = 280
# The filename is chosen by whoever uploads the file, so it is untrusted metadata
# with no evidentiary value: renaming a document changes nothing about what is
# inside it. The masked name stays in the audit trail, but the models are given a
# fixed label instead, so a verdict can never depend on how a file was called.
DOCUMENT_EVALUATION_LABEL = "Documento adjunto"


class SecurityAnalysisCommandServiceImpl(SecurityAnalysisCommandService):
    """
    Runs the deterministic scan, the masking, the contextual evaluation and the
    final risk calculation for a prompt or for a supported document.

    Two rules drive the whole flow. First, an execution recorded as running must
    always reach a terminal state: any failure, expected or not, is written back
    as FAILED before the error propagates, so a crash can never leave a document
    permanently locked. Second, a model failure is never turned into a low risk;
    it clears the risk values instead.
    """

    def __init__(
        self,
        analysis_repository: SecurityAnalysisRepository,
        ollama_security_analysis_client: OllamaSecurityAnalysisClient,
        ollama_sensitive_content_discovery_client: OllamaSensitiveContentDiscoveryClient,
        security_model_name: str,
        document_source_service: DocumentSourceService | None = None,
        document_text_extractor: DocumentTextExtractor | None = None,
        prompt_max_length: int = 8000,
        prompt_min_length: int = 3,
        sensitive_data_detection_service: SensitiveDataDetectionService | None = None,
        prompt_detection_service: PromptSensitiveDataDetectionService | None = None,
        document_free_text_detection_service: DocumentFreeTextSensitiveDataDetectionService
        | None = None,
        content_sanitization_service: ContentSanitizationService | None = None,
        document_structure_summarizer: DocumentStructureSummarizer | None = None,
        prompt_content_summarizer: PromptContentSummarizer | None = None,
        risk_calculation_service: RiskCalculationService | None = None,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._ollama_client = ollama_security_analysis_client
        self._discovery_client = ollama_sensitive_content_discovery_client
        self._security_model_name = security_model_name
        self._document_source_service = document_source_service
        self._document_text_extractor = document_text_extractor
        self._prompt_max_length = prompt_max_length
        self._prompt_min_length = prompt_min_length
        self._detector = sensitive_data_detection_service or SensitiveDataDetectionService()
        self._prompt_detector = prompt_detection_service or PromptSensitiveDataDetectionService()
        self._document_free_text_detector = (
            document_free_text_detection_service
            or DocumentFreeTextSensitiveDataDetectionService(self._prompt_detector)
        )
        self._sanitizer = content_sanitization_service or ContentSanitizationService()
        self._summarizer = document_structure_summarizer or DocumentStructureSummarizer()
        self._prompt_summarizer = prompt_content_summarizer or PromptContentSummarizer(
            self._prompt_detector
        )
        self._risk_calculator = risk_calculation_service or RiskCalculationService()
        self.published_events: list[object] = []
        # Identifier of the most recent execution this service started. Callers that
        # catch a failure use it to read back the persisted FAILED row instead of
        # inventing an assessment of their own.
        self.last_analysis_id: int | None = None

    async def handle_analyze_prompt(self, command: AnalyzePromptCommand) -> SecurityAnalysis:
        prompt = self._normalize_prompt(command.prompt)
        analysis = SecurityAnalysis.start_for_prompt(
            content_reference="Consulta escrita",
            content_fingerprint=self._fingerprint(prompt.encode("utf-8")),
            content_length=len(prompt),
            masked_preview=self._masked_preview(prompt),
            model_name=self._security_model_name,
        )
        analysis = await self._analysis_repository.save(analysis)
        self._publish_started(analysis)

        async def run() -> SecurityAnalysis:
            findings = self._prompt_detector.scan(prompt)
            summary = self._prompt_summarizer.summarize(prompt, findings)
            context = SecurityEvaluationContext(
                content_type=AnalyzedContentType.PROMPT,
                reference_label=analysis.content_reference,
                approximate_size=summary.character_count,
                estimated_subjects=summary.estimated_subjects,
                truncated=summary.truncated,
                structure=summary.to_prompt_payload(),
            )
            interpretation = await self._ollama_client.evaluate(context=context, findings=findings)
            assessment = self._risk_calculator.calculate(
                findings=findings,
                estimated_subjects=summary.estimated_subjects,
                interpretation=interpretation,
            )
            analysis.complete(
                risk_level=assessment.risk_level,
                secrets_risk=assessment.secrets_risk,
                personal_data_risk=assessment.personal_data_risk,
                confidence=assessment.confidence,
                tampering_suspected=assessment.tampering_suspected,
                data_categories=list(assessment.data_categories),
                estimated_subjects=assessment.estimated_subjects,
                summary=self._build_summary(interpretation.summary, assessment.risk_level.value),
                rationale=self._build_rationale(interpretation.rationale, findings),
                findings=findings,
                content_truncated=summary.truncated,
            )
            return await self._analysis_repository.save(analysis)

        return await self._execute(analysis, run)

    async def handle_analyze_document(self, command: AnalyzeDocumentCommand) -> SecurityAnalysis:
        if self._document_source_service is None or self._document_text_extractor is None:
            raise DocumentSourceNotFoundError("Document analysis is not available in this context")

        source = await self._document_source_service.get_document_source(command.document_id)
        if source is None:
            raise DocumentSourceNotFoundError("Document not found")

        analysis = SecurityAnalysis.start_for_document(
            document_id=source.document_id,
            content_reference=mask_free_text(source.display_name),
            content_fingerprint=self._fingerprint(
                f"document:{source.document_id}".encode()
            ),
            content_length=source.size_bytes,
            masked_preview=mask_free_text(source.display_name),
            model_name=self._security_model_name,
        )
        analysis = await self._analysis_repository.save(analysis)
        self._publish_started(analysis)

        async def run() -> SecurityAnalysis:
            content = await self._document_source_service.read_document_content(
                source.document_id
            )
            extracted_document = await self._document_text_extractor.extract_content(
                content,
                source.mime_type,
                source.display_name,
            )
            analysis.content_fingerprint = self._fingerprint(content)
            discovery = await self._discovery_client.inspect(
                content=extracted_document,
                reference_label=DOCUMENT_EVALUATION_LABEL,
            )
            findings = self._merge_findings(
                self._detector.scan(extracted_document),
                self._document_free_text_detector.scan(extracted_document),
            )
            sanitized_content = self._sanitizer.sanitize(extracted_document, findings)
            structure = self._summarizer.summarize(
                content=extracted_document,
                sanitized_content=sanitized_content,
                findings=findings,
                approximate_size_bytes=len(content),
            )
            context = SecurityEvaluationContext(
                content_type=AnalyzedContentType.DOCUMENT,
                reference_label=DOCUMENT_EVALUATION_LABEL,
                approximate_size=structure.approximate_size_bytes,
                estimated_subjects=structure.estimated_subjects,
                truncated=structure.truncated,
                structure=structure.to_prompt_payload(),
            )
            interpretation = await self._ollama_client.evaluate(context=context, findings=findings)
            assessment = self._risk_calculator.calculate(
                findings=findings,
                estimated_subjects=structure.estimated_subjects,
                interpretation=interpretation,
                discovery=discovery,
            )
            confirmed_discovery = discovery if assessment.discovery_confirmed else None
            analysis.complete(
                risk_level=assessment.risk_level,
                secrets_risk=assessment.secrets_risk,
                personal_data_risk=assessment.personal_data_risk,
                confidence=assessment.confidence,
                tampering_suspected=assessment.tampering_suspected,
                data_categories=list(assessment.data_categories),
                estimated_subjects=assessment.estimated_subjects,
                summary=self._build_summary(
                    interpretation.summary,
                    assessment.risk_level.value,
                    confirmed_discovery,
                ),
                rationale=self._build_rationale(
                    interpretation.rationale,
                    findings,
                    confirmed_discovery,
                ),
                findings=findings,
                content_truncated=structure.truncated,
            )
            return await self._analysis_repository.save(analysis)

        return await self._execute(analysis, run)

    async def _execute(self, analysis: SecurityAnalysis, run) -> SecurityAnalysis:
        try:
            completed = await run()
        except Exception as error:
            failed = await self._record_failure(analysis, error)
            if isinstance(
                error,
                (
                    AnalysisModelError,
                    DocumentContentExtractionError,
                    DocumentContentReadError,
                ),
            ):
                raise
            logger.exception("Unexpected failure while analyzing content")
            raise AnalysisExecutionError(
                failed.error_message or "The security review could not be completed."
            ) from error

        self.published_events.append(
            SecurityAnalysisCompletedEvent(
                analysis_id=completed.id or 0,
                content_type=completed.content_type,
                risk_level=completed.risk_level,
                document_id=completed.document_id,
            )
        )
        return completed

    async def _record_failure(
        self,
        analysis: SecurityAnalysis,
        error: Exception,
    ) -> SecurityAnalysis:
        analysis.fail(self._safe_error_message(error))
        try:
            failed = await self._analysis_repository.save(analysis)
        except Exception:
            logger.exception("The failed analysis state could not be persisted")
            return analysis
        self.published_events.append(
            SecurityAnalysisFailedEvent(
                analysis_id=failed.id or 0,
                content_type=failed.content_type,
                document_id=failed.document_id,
            )
        )
        return failed

    def _publish_started(self, analysis: SecurityAnalysis) -> None:
        self.last_analysis_id = analysis.id
        self.published_events.append(
            SecurityAnalysisStartedEvent(
                analysis_id=analysis.id or 0,
                content_type=analysis.content_type,
                document_id=analysis.document_id,
            )
        )

    def _normalize_prompt(self, prompt: str) -> str:
        normalized = prompt.replace("\r\n", "\n").strip()
        if not normalized:
            raise InvalidPromptError("La consulta no puede estar vacía.")
        if len(normalized) < self._prompt_min_length:
            raise InvalidPromptError(
                f"La consulta debe tener al menos {self._prompt_min_length} caracteres."
            )
        if len(normalized) > self._prompt_max_length:
            raise InvalidPromptError(
                f"La consulta supera el límite de {self._prompt_max_length} caracteres."
            )
        return normalized

    def _masked_preview(self, prompt: str) -> str:
        return self._prompt_detector.mask_text(prompt[:MASKED_PREVIEW_MAX_CHARACTERS])

    def _fingerprint(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _build_summary(
        self,
        model_summary: str,
        final_risk: str,
        discovery: SensitiveContentDiscovery | None = None,
    ) -> str:
        discovery_summary = ""
        if discovery is not None and discovery.contains_sensitive_data:
            categories = ", ".join(discovery.data_categories)
            discovery_summary = (
                f"La inspección local de contenido detectó categorías sensibles: {categories}. "
            )
        return f"{discovery_summary}{model_summary} Riesgo final: {final_risk}."

    def _build_rationale(
        self,
        model_rationale: str,
        findings: list[object],
        discovery: SensitiveContentDiscovery | None = None,
    ) -> str:
        discovery_note = (
            " La primera pasada de IA local clasificó el contenido sensible sin conservar valores."
            if discovery is not None and discovery.contains_sensitive_data
            else ""
        )
        return (
            f"{model_rationale} El análisis determinista produjo {len(findings)} hallazgo(s) "
            "enmascarado(s); el riesgo final nunca reduce la evidencia determinista confirmada."
            f"{discovery_note}"
        )

    def _merge_findings(
        self,
        *finding_groups: list[AnalysisFinding],
    ) -> list[AnalysisFinding]:
        grouped: dict[tuple[str, str, str], AnalysisFinding] = {}
        for finding in (finding for group in finding_groups for finding in group):
            key = (
                finding.finding_type.value,
                finding.json_path,
                finding.masked_evidence,
            )
            existing = grouped.get(key)
            if existing is None:
                grouped[key] = finding
                continue
            methods = sorted(
                {
                    *existing.detection_method.split("+"),
                    *finding.detection_method.split("+"),
                }
            )
            grouped[key] = replace(
                existing,
                detection_method="+".join(methods),
                occurrences=max(existing.occurrences, finding.occurrences),
                is_placeholder=existing.is_placeholder and finding.is_placeholder,
            )
        return [
            replace(finding, finding_id=f"f{index}")
            for index, finding in enumerate(grouped.values(), start=1)
        ]

    def _safe_error_message(self, error: Exception) -> str:
        if isinstance(error, AnalysisModelTimeoutError):
            return "El analizador de seguridad no respondió dentro del tiempo configurado."
        if isinstance(error, AnalysisModelUnavailableError):
            return "El analizador de seguridad local no está disponible."
        if isinstance(error, AnalysisModelError):
            return "El analizador de seguridad no devolvió una respuesta válida."
        if isinstance(error, DocumentContentReadError):
            return "El contenido almacenado del documento no pudo leerse de forma segura."
        if isinstance(error, DocumentContentExtractionError):
            return "El documento almacenado no pudo convertirse en contenido analizable."
        return "La revisión de seguridad no pudo completarse."
