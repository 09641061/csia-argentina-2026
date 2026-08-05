from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.application.internal.services.sensitive_value_masking import (
    mask_sensitive_value,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.entities.security_analysis import SecurityAnalysis
from app.analysis.domain.model.valueobjects.analysis_confidence import AnalysisConfidence
from app.analysis.domain.model.valueobjects.analysis_finding_severity import (
    AnalysisFindingSeverity,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import AnalysisFindingType
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.model.valueobjects.analysis_status import AnalysisStatus
from app.analysis.domain.model.valueobjects.analyzed_content_type import AnalyzedContentType
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.secrets_risk_level import SecretsRiskLevel
from app.analysis.domain.repositories.security_analysis_repository import (
    SecurityAnalysisRepository,
)
from app.analysis.infrastructure.persistence.sqlalchemy.models.security_analysis_model import (
    SecurityAnalysisModel,
)


class SqlAlchemySecurityAnalysisRepository(SecurityAnalysisRepository):
    """
    Stages analysis changes on the session; the unit of work commits.

    The running row is flushed so the entity gets its identity, and it is only
    durable once the application service decides the checkpoint is consistent.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, analysis: SecurityAnalysis) -> SecurityAnalysis:
        model: SecurityAnalysisModel | None = None
        if analysis.id is not None:
            model = await self._session.scalar(
                select(SecurityAnalysisModel).where(SecurityAnalysisModel.id == analysis.id)
            )
            if model is None:
                raise ValueError("Analysis not found")

        if model is None:
            model = SecurityAnalysisModel(
                content_type=analysis.content_type.value,
                document_id=analysis.document_id,
                content_reference=analysis.content_reference,
                content_fingerprint=analysis.content_fingerprint,
                content_length=analysis.content_length,
                masked_preview=analysis.masked_preview,
                status=analysis.status.value,
                estimated_subjects=analysis.estimated_subjects.value,
                model_name=analysis.model_name,
                data_categories=[],
                findings=[],
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
            )
            self._session.add(model)

        self._copy_to_model(analysis, model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def find_by_id(self, analysis_id: int) -> SecurityAnalysis | None:
        model = await self._session.scalar(
            select(SecurityAnalysisModel).where(SecurityAnalysisModel.id == analysis_id)
        )
        return self._to_domain(model) if model is not None else None

    async def find_latest_by_document_id(self, document_id: int) -> SecurityAnalysis | None:
        model = await self._session.scalar(
            select(SecurityAnalysisModel)
            .where(SecurityAnalysisModel.document_id == document_id)
            .order_by(SecurityAnalysisModel.id.desc())
            .limit(1)
        )
        return self._to_domain(model) if model is not None else None

    async def list(self, page: int, page_size: int) -> tuple[list[SecurityAnalysis], int]:
        total = await self._session.scalar(select(func.count(SecurityAnalysisModel.id)))
        result = await self._session.execute(
            select(SecurityAnalysisModel)
            .order_by(SecurityAnalysisModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [self._to_domain(model) for model in result.scalars().all()], int(total or 0)

    def _copy_to_model(self, analysis: SecurityAnalysis, model: SecurityAnalysisModel) -> None:
        model.content_type = analysis.content_type.value
        model.document_id = analysis.document_id
        model.content_reference = analysis.content_reference
        model.content_fingerprint = analysis.content_fingerprint
        model.content_length = analysis.content_length
        model.masked_preview = analysis.masked_preview
        model.status = analysis.status.value
        model.risk_level = analysis.risk_level.value if analysis.risk_level else None
        model.secrets_risk = analysis.secrets_risk.value if analysis.secrets_risk else None
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
        model.findings = [self._finding_to_payload(finding) for finding in analysis.findings]
        model.content_truncated = analysis.content_truncated
        model.error_message = analysis.error_message
        model.analyzed_at = analysis.analyzed_at
        model.updated_at = analysis.updated_at

    def _to_domain(self, model: SecurityAnalysisModel) -> SecurityAnalysis:
        return SecurityAnalysis(
            id=model.id,
            content_type=AnalyzedContentType(model.content_type),
            document_id=model.document_id,
            content_reference=model.content_reference,
            content_fingerprint=model.content_fingerprint,
            content_length=model.content_length,
            masked_preview=model.masked_preview,
            model_name=model.model_name,
            status=AnalysisStatus(model.status),
            risk_level=AnalysisRiskLevel(model.risk_level) if model.risk_level else None,
            secrets_risk=SecretsRiskLevel(model.secrets_risk) if model.secrets_risk else None,
            personal_data_risk=AnalysisRiskLevel(model.personal_data_risk)
            if model.personal_data_risk
            else None,
            confidence=AnalysisConfidence(model.confidence) if model.confidence else None,
            tampering_suspected=model.tampering_suspected,
            data_categories=list(model.data_categories or []),
            estimated_subjects=EstimatedSubjects(model.estimated_subjects),
            summary=model.summary,
            rationale=model.rationale,
            findings=[self._payload_to_finding(payload) for payload in model.findings or []],
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
        evidence = str(payload.get("masked_evidence", "[REDACTED]"))
        if "*" not in evidence and not evidence.startswith("[REDACTED"):
            evidence = mask_sensitive_value(evidence, finding_type)
        return AnalysisFinding(
            finding_id=str(payload.get("finding_id", "f1")),
            finding_type=finding_type,
            severity=AnalysisFindingSeverity(str(payload["severity"])),
            title=str(payload["title"]),
            description=str(payload["description"]),
            json_path=str(payload.get("json_path", "$")),
            evidence=evidence,
            detection_method=str(payload.get("detection_method", "pattern")),
            confidence=AnalysisConfidence(str(payload.get("confidence", "medium"))),
            occurrences=int(payload.get("occurrences", 1)),
            data_category=str(payload["data_category"]) if payload.get("data_category") else None,
            is_placeholder=bool(payload.get("is_placeholder", False)),
        )
