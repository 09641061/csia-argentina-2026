from __future__ import annotations

from app.analysis.application.internal.outboundservices.document_content_downloader import (
    DocumentContentDownloader,
)
from app.analysis.application.internal.outboundservices.document_source_service import (
    DocumentSourceService,
)
from app.analysis.application.internal.outboundservices.document_text_extractor import (
    DocumentTextExtractor,
)
from app.analysis.application.internal.outboundservices.ollama_analysis_client import (
    OllamaAnalysisClient,
)
from app.analysis.application.internal.services.content_sanitization_service import (
    ContentSanitizationService,
)
from app.analysis.application.internal.services.document_structure_summarizer import (
    DocumentStructureSummarizer,
)
from app.analysis.application.internal.services.risk_calculation_service import (
    RiskCalculationService,
)
from app.analysis.application.internal.services.sensitive_data_detection_service import (
    SensitiveDataDetectionService,
)
from app.analysis.domain.exceptions import (
    AnalysisConflictError,
    AnalysisModelError,
    AnalysisModelTimeoutError,
    DocumentContentDownloadError,
    DocumentContentExtractionError,
    DocumentSourceNotFoundError,
)
from app.analysis.domain.model.commands.analyze_document_command import (
    AnalyzeDocumentCommand,
)
from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis
from app.analysis.domain.model.events.document_analysis_completed_event import (
    DocumentAnalysisCompletedEvent,
)
from app.analysis.domain.model.events.document_analysis_failed_event import (
    DocumentAnalysisFailedEvent,
)
from app.analysis.domain.model.events.document_analysis_started_event import (
    DocumentAnalysisStartedEvent,
)
from app.analysis.domain.repositories.document_analysis_repository import (
    DocumentAnalysisRepository,
)
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
        sensitive_data_detection_service: SensitiveDataDetectionService | None = None,
        content_sanitization_service: ContentSanitizationService | None = None,
        document_structure_summarizer: DocumentStructureSummarizer | None = None,
        risk_calculation_service: RiskCalculationService | None = None,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._document_source_service = document_source_service
        self._document_content_downloader = document_content_downloader
        self._document_text_extractor = document_text_extractor
        self._ollama_analysis_client = ollama_analysis_client
        self._ollama_model_name = ollama_model_name
        self._detector = (
            sensitive_data_detection_service or SensitiveDataDetectionService()
        )
        self._sanitizer = content_sanitization_service or ContentSanitizationService()
        self._summarizer = (
            document_structure_summarizer or DocumentStructureSummarizer()
        )
        self._risk_calculator = risk_calculation_service or RiskCalculationService()
        self.published_events: list[object] = []

    async def handle_analyze_document(
        self, command: AnalyzeDocumentCommand
    ) -> DocumentAnalysis:
        active_analysis = await self._analysis_repository.find_active_by_document_id(
            command.document_id
        )
        if active_analysis is not None:
            raise AnalysisConflictError(
                "An analysis is already running for this document"
            )

        source = await self._document_source_service.get_document_reference(
            command.document_id
        )
        if source is None:
            raise DocumentSourceNotFoundError("Document not found")

        analysis = DocumentAnalysis.create_pending(
            document_id=source.document_id,
            source_filename=source.original_filename,
            source_mime_type=source.mime_type,
            source_document_url=source.document_url,
            source_size_bytes=source.size_bytes,
            model_name=self._ollama_model_name,
        )
        analysis = await self._analysis_repository.save(analysis)
        self.published_events.append(
            DocumentAnalysisStartedEvent(
                analysis_id=analysis.id or 0,
                document_id=analysis.document_id,
            )
        )

        try:
            content = await self._document_content_downloader.download(
                source.document_url
            )
            parsed_json = self._document_text_extractor.extract_json(
                content,
                source.mime_type,
                source.original_filename,
            )
            findings = self._detector.scan(parsed_json)
            sanitized_content = self._sanitizer.sanitize(parsed_json, findings)
            structure = self._summarizer.summarize(
                content=parsed_json,
                sanitized_content=sanitized_content,
                findings=findings,
                approximate_size_bytes=len(content),
            )
            interpretation = await self._ollama_analysis_client.analyze(
                source=source,
                structure=structure,
                findings=findings,
            )
            assessment = self._risk_calculator.calculate(
                findings=findings,
                structure=structure,
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
                summary=self._build_summary(
                    interpretation.summary, assessment.risk_level.value
                ),
                rationale=self._build_rationale(interpretation.rationale, findings),
                findings=findings,
                sanitized_content=sanitized_content,
                content_truncated=structure.truncated,
            )
            analysis = await self._analysis_repository.save(analysis)
        except (
            DocumentContentDownloadError,
            DocumentContentExtractionError,
            AnalysisModelError,
        ) as error:
            analysis.fail(self._safe_error_message(error))
            analysis = await self._analysis_repository.save(analysis)
            self.published_events.append(
                DocumentAnalysisFailedEvent(
                    analysis_id=analysis.id or 0,
                    document_id=analysis.document_id,
                )
            )
            raise

        self.published_events.append(
            DocumentAnalysisCompletedEvent(
                analysis_id=analysis.id or 0,
                document_id=analysis.document_id,
                risk_level=analysis.risk_level,
            )
        )
        return analysis

    def _build_summary(self, model_summary: str, final_risk: str) -> str:
        return f"{model_summary} Final risk: {final_risk}."

    def _build_rationale(self, model_rationale: str, findings: list[object]) -> str:
        return (
            f"{model_rationale} Deterministic scan produced {len(findings)} masked finding(s); "
            "the final risk never lowers confirmed deterministic evidence."
        )

    def _safe_error_message(self, error: Exception) -> str:
        if isinstance(error, AnalysisModelTimeoutError):
            return "Ollama did not respond before the configured timeout."
        if isinstance(error, AnalysisModelError):
            return "Ollama analysis did not complete with a valid response."
        if isinstance(error, DocumentContentDownloadError):
            return "The stored document content could not be downloaded safely."
        return "The stored document could not be parsed as an analyzable JSON object or array."
