from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.application.internal.services.sensitive_value_masking import (
    mask_sensitive_value,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis
from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_finding_severity import (
    AnalysisFindingSeverity,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.analysis_status import AnalysisStatus
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel
from app.analysis.domain.repositories.document_analysis_repository import (
    DocumentAnalysisRepository,
)
from app.analysis.infrastructure.persistence.sqlalchemy.models.document_analysis_model import (
    DocumentAnalysisModel,
)


class SqlAlchemyDocumentAnalysisRepository(DocumentAnalysisRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        model: DocumentAnalysisModel | None = None
        if analysis.id is not None:
            model = await self._session.scalar(
                select(DocumentAnalysisModel).where(
                    DocumentAnalysisModel.id == analysis.id
                )
            )
            if model is None:
                raise ValueError("Analysis not found")
        if model is None:
            model = DocumentAnalysisModel(
                document_id=analysis.document_id,
                source_filename=analysis.source_filename,
                source_mime_type=analysis.source_mime_type,
                source_document_url=analysis.source_document_url,
                source_size_bytes=analysis.source_size_bytes,
                status=analysis.status.value,
                risk_level=None,
                secrets_risk=None,
                personal_data_risk=None,
                confidence=None,
                tampering_suspected=False,
                data_categories=[],
                estimated_subjects=analysis.estimated_subjects.value,
                summary="",
                rationale="",
                explanation="",
                model_name=analysis.model_name,
                findings=[],
                sanitized_content=None,
                content_truncated=False,
                error_message=None,
                analyzed_at=None,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
            )
            self._session.add(model)

        self._copy_to_model(analysis, model)
        await self._session.flush()
        await self._session.refresh(model)
        await self._session.commit()
        return self._to_domain(model)

    async def find_by_document_id(self, document_id: int) -> DocumentAnalysis | None:
        model = await self._session.scalar(
            select(DocumentAnalysisModel)
            .where(DocumentAnalysisModel.document_id == document_id)
            .order_by(DocumentAnalysisModel.id.desc())
            .limit(1)
        )
        return self._to_domain(model) if model is not None else None

    async def find_by_id(self, analysis_id: int) -> DocumentAnalysis | None:
        model = await self._session.scalar(
            select(DocumentAnalysisModel).where(DocumentAnalysisModel.id == analysis_id)
        )
        return self._to_domain(model) if model is not None else None

    async def find_active_by_document_id(
        self, document_id: int
    ) -> DocumentAnalysis | None:
        model = await self._session.scalar(
            select(DocumentAnalysisModel)
            .where(
                DocumentAnalysisModel.document_id == document_id,
                DocumentAnalysisModel.status == AnalysisStatus.RUNNING.value,
            )
            .order_by(DocumentAnalysisModel.id.desc())
            .limit(1)
        )
        return self._to_domain(model) if model is not None else None

    async def list(
        self, page: int, page_size: int
    ) -> tuple[list[DocumentAnalysis], int]:
        total = await self._session.scalar(select(func.count(DocumentAnalysisModel.id)))
        result = await self._session.execute(
            select(DocumentAnalysisModel)
            .order_by(DocumentAnalysisModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [self._to_domain(model) for model in result.scalars().all()], int(
            total or 0
        )

    def _copy_to_model(
        self, analysis: DocumentAnalysis, model: DocumentAnalysisModel
    ) -> None:
        model.document_id = analysis.document_id
        model.source_filename = analysis.source_filename
        model.source_mime_type = analysis.source_mime_type
        model.source_document_url = analysis.source_document_url
        model.source_size_bytes = analysis.source_size_bytes
        model.status = analysis.status.value
        model.risk_level = analysis.risk_level.value if analysis.risk_level else None
        model.secrets_risk = (
            analysis.secrets_risk.value if analysis.secrets_risk else None
        )
        model.personal_data_risk = (
            analysis.personal_data_risk.value if analysis.personal_data_risk else None
        )
        model.confidence = analysis.confidence.value if analysis.confidence else None
        model.tampering_suspected = analysis.tampering_suspected
        model.data_categories = list(analysis.data_categories)
        model.estimated_subjects = analysis.estimated_subjects.value
        model.summary = analysis.summary
        model.rationale = analysis.rationale
        model.explanation = analysis.explanation
        model.model_name = analysis.model_name
        model.findings = [
            self._finding_to_payload(finding) for finding in analysis.findings
        ]
        model.sanitized_content = analysis.sanitized_content
        model.content_truncated = analysis.content_truncated
        model.error_message = analysis.error_message
        model.analyzed_at = analysis.analyzed_at
        model.created_at = analysis.created_at
        model.updated_at = analysis.updated_at

    def _to_domain(self, model: DocumentAnalysisModel) -> DocumentAnalysis:
        return DocumentAnalysis(
            id=model.id,
            document_id=model.document_id,
            source_filename=model.source_filename,
            source_mime_type=model.source_mime_type,
            source_document_url=model.source_document_url,
            source_size_bytes=model.source_size_bytes,
            model_name=model.model_name,
            status=AnalysisStatus(model.status),
            risk_level=AnalysisRiskLevel(model.risk_level)
            if model.risk_level
            else None,
            secrets_risk=SecretsRiskLevel(model.secrets_risk)
            if model.secrets_risk
            else None,
            personal_data_risk=AnalysisRiskLevel(model.personal_data_risk)
            if model.personal_data_risk
            else None,
            confidence=AnalysisConfidence(model.confidence)
            if model.confidence
            else None,
            tampering_suspected=model.tampering_suspected,
            data_categories=list(model.data_categories or []),
            estimated_subjects=EstimatedSubjects(model.estimated_subjects),
            summary=model.summary,
            rationale=model.rationale,
            findings=[
                self._payload_to_finding(payload) for payload in model.findings or []
            ],
            sanitized_content=model.sanitized_content,
            content_truncated=model.content_truncated,
            error_message=model.error_message,
            analyzed_at=model.analyzed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _finding_to_payload(self, finding: AnalysisFinding) -> dict[str, object]:
        return {
            "finding_id": finding.finding_id,
            "finding_type": finding.finding_type.value,
            "severity": finding.severity.value,
            "title": finding.title,
            "description": finding.description,
            "json_path": finding.json_path,
            "masked_evidence": finding.masked_evidence,
            "detection_method": finding.detection_method,
            "confidence": finding.confidence.value,
            "occurrences": finding.occurrences,
            "data_category": finding.data_category,
            "is_placeholder": finding.is_placeholder,
        }

    def _payload_to_finding(self, payload: dict[str, object]) -> AnalysisFinding:
        finding_type = AnalysisFindingType(str(payload["finding_type"]))
        evidence = str(
            payload.get("masked_evidence", payload.get("evidence", "[REDACTED]"))
        )
        if "*" not in evidence and not evidence.startswith("[REDACTED"):
            evidence = mask_sensitive_value(evidence, finding_type)
        return AnalysisFinding(
            finding_id=str(payload.get("finding_id", "legacy-finding")),
            finding_type=finding_type,
            severity=AnalysisFindingSeverity(str(payload["severity"])),
            title=str(payload["title"]),
            description=str(payload["description"]),
            json_path=str(payload.get("json_path", "$")),
            evidence=evidence,
            detection_method=str(payload.get("detection_method", "legacy_pattern")),
            confidence=AnalysisConfidence(str(payload.get("confidence", "medium"))),
            occurrences=int(payload.get("occurrences", 1)),
            data_category=str(payload["data_category"])
            if payload.get("data_category")
            else None,
            is_placeholder=bool(payload.get("is_placeholder", False)),
        )
