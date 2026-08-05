from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.decision.domain.model.entities.secure_interaction import SecureInteraction
from app.decision.domain.model.valueobjects.decision_reason_code import DecisionReasonCode
from app.decision.domain.model.valueobjects.generation_status import GenerationStatus
from app.decision.domain.model.valueobjects.interaction_content_type import (
    InteractionContentType,
)
from app.decision.domain.model.valueobjects.masked_finding_summary import MaskedFindingSummary
from app.decision.domain.model.valueobjects.security_decision import SecurityDecision
from app.decision.domain.repositories.secure_interaction_repository import (
    SecureInteractionRepository,
)
from app.decision.infrastructure.persistence.sqlalchemy.models.secure_interaction_model import (
    SecureInteractionModel,
)


class SqlAlchemySecureInteractionRepository(SecureInteractionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, interaction: SecureInteraction) -> SecureInteraction:
        model: SecureInteractionModel | None = None
        if interaction.id is not None:
            model = await self._session.scalar(
                select(SecureInteractionModel).where(SecureInteractionModel.id == interaction.id)
            )
            if model is None:
                raise ValueError("Interaction not found")

        if model is None:
            model = SecureInteractionModel(created_at=interaction.created_at)
            self._session.add(model)

        model.content_type = interaction.content_type.value
        model.decision = interaction.decision.value
        model.reason_code = interaction.reason_code.value
        model.reason = interaction.reason
        model.content_reference = interaction.content_reference
        model.risk_level = interaction.risk_level
        model.prompt_analysis_id = interaction.prompt_analysis_id
        model.document_analysis_id = interaction.document_analysis_id
        model.document_id = interaction.document_id
        model.masked_findings = [
            self._finding_to_payload(finding) for finding in interaction.masked_findings
        ]
        model.data_categories = list(interaction.data_categories)
        model.generation_status = interaction.generation_status.value
        model.generation_model = interaction.generation_model
        model.generation_error = interaction.generation_error
        model.generated_at = interaction.generated_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def find_by_id(self, interaction_id: int) -> SecureInteraction | None:
        model = await self._session.scalar(
            select(SecureInteractionModel).where(SecureInteractionModel.id == interaction_id)
        )
        return self._to_domain(model) if model is not None else None

    async def list(self, page: int, page_size: int) -> tuple[list[SecureInteraction], int]:
        total = await self._session.scalar(select(func.count(SecureInteractionModel.id)))
        result = await self._session.execute(
            select(SecureInteractionModel)
            .order_by(SecureInteractionModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [self._to_domain(model) for model in result.scalars().all()], int(total or 0)

    def _finding_to_payload(self, finding: MaskedFindingSummary) -> dict[str, object]:
        return {
            "origin": finding.origin,
            "finding_type": finding.finding_type,
            "severity": finding.severity,
            "title": finding.title,
            "location": finding.location,
            "masked_evidence": finding.masked_evidence,
            "occurrences": finding.occurrences,
            "is_placeholder": finding.is_placeholder,
        }

    def _payload_to_finding(self, payload: dict[str, object]) -> MaskedFindingSummary:
        return MaskedFindingSummary(
            origin=str(payload.get("origin", "document")),
            finding_type=str(payload.get("finding_type", "other")),
            severity=str(payload.get("severity", "medium")),
            title=str(payload.get("title", "Hallazgo")),
            location=str(payload.get("location", "$")),
            masked_evidence=str(payload.get("masked_evidence", "[REDACTED]")),
            occurrences=int(payload.get("occurrences", 1)),
            is_placeholder=bool(payload.get("is_placeholder", False)),
        )

    def _to_domain(self, model: SecureInteractionModel) -> SecureInteraction:
        return SecureInteraction(
            id=model.id,
            content_type=InteractionContentType(model.content_type),
            decision=SecurityDecision(model.decision),
            reason_code=DecisionReasonCode(model.reason_code),
            reason=model.reason,
            content_reference=model.content_reference,
            risk_level=model.risk_level,
            prompt_analysis_id=model.prompt_analysis_id,
            document_analysis_id=model.document_analysis_id,
            document_id=model.document_id,
            masked_findings=[
                self._payload_to_finding(payload) for payload in model.masked_findings or []
            ],
            data_categories=list(model.data_categories or []),
            generation_status=GenerationStatus(model.generation_status),
            generation_model=model.generation_model,
            generation_error=model.generation_error,
            generated_at=model.generated_at,
            created_at=model.created_at,
        )
