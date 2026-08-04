from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.entities.document_analysis import DocumentAnalysis
from app.analysis.domain.model.valueobjects.analysis_finding_severity import AnalysisFindingSeverity
from app.analysis.domain.model.valueobjects.analysis_finding_type import AnalysisFindingType
from app.analysis.domain.model.valueobjects.analysis_risk_level import AnalysisRiskLevel
from app.analysis.domain.repositories.document_analysis_repository import DocumentAnalysisRepository
from app.analysis.infrastructure.persistence.sqlalchemy.models.document_analysis_model import (
    DocumentAnalysisModel,
)


class SqlAlchemyDocumentAnalysisRepository(DocumentAnalysisRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        result = await self._session.execute(
            select(DocumentAnalysisModel).where(DocumentAnalysisModel.document_id == analysis.document_id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = DocumentAnalysisModel(
                document_id=analysis.document_id,
                source_filename=analysis.source_filename,
                source_mime_type=analysis.source_mime_type,
                source_document_url=analysis.source_document_url,
                risk_level=analysis.risk_level.value,
                explanation=analysis.explanation,
                model_name=analysis.model_name,
                findings=[self._finding_to_payload(finding) for finding in analysis.findings],
                analyzed_at=analysis.analyzed_at,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
            )
            self._session.add(model)
        else:
            model.source_filename = analysis.source_filename
            model.source_mime_type = analysis.source_mime_type
            model.source_document_url = analysis.source_document_url
            model.risk_level = analysis.risk_level.value
            model.explanation = analysis.explanation
            model.model_name = analysis.model_name
            model.findings = [self._finding_to_payload(finding) for finding in analysis.findings]
            model.analyzed_at = analysis.analyzed_at
            model.updated_at = analysis.updated_at

        await self._session.flush()
        await self._session.refresh(model)
        await self._session.commit()
        return self._to_domain(model)

    async def find_by_document_id(self, document_id: int) -> DocumentAnalysis | None:
        result = await self._session.execute(
            select(DocumentAnalysisModel).where(DocumentAnalysisModel.document_id == document_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def list(self, page: int, page_size: int) -> tuple[list[DocumentAnalysis], int]:
        total = await self._session.scalar(select(func.count(DocumentAnalysisModel.id)))
        total_records = int(total or 0)
        result = await self._session.execute(
            select(DocumentAnalysisModel)
            .order_by(DocumentAnalysisModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = list(result.scalars().all())
        return [self._to_domain(model) for model in models], total_records

    def _to_domain(self, model: DocumentAnalysisModel) -> DocumentAnalysis:
        findings = [self._payload_to_finding(payload) for payload in model.findings or []]
        return DocumentAnalysis(
            id=model.id,
            document_id=model.document_id,
            source_filename=model.source_filename,
            source_mime_type=model.source_mime_type,
            source_document_url=model.source_document_url,
            risk_level=AnalysisRiskLevel(model.risk_level),
            explanation=model.explanation,
            model_name=model.model_name,
            findings=findings,
            analyzed_at=model.analyzed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _finding_to_payload(self, finding: AnalysisFinding) -> dict[str, str]:
        return {
            "finding_type": finding.finding_type.value,
            "severity": finding.severity.value,
            "title": finding.title,
            "description": finding.description,
            "evidence": finding.evidence,
        }

    def _payload_to_finding(self, payload: dict[str, str]) -> AnalysisFinding:
        return AnalysisFinding(
            finding_type=AnalysisFindingType(payload["finding_type"]),
            severity=AnalysisFindingSeverity(payload["severity"]),
            title=payload["title"],
            description=payload["description"],
            evidence=payload["evidence"],
        )

