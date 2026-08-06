from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.persistence.sqlalchemy.base import Base


class SecureInteractionModel(Base):
    """
    Audit record of one secure query.

    There is no column for the prompt, the document content or the generated
    answer. Explaining a decision later needs the verdict, the reason, the risk
    and the masked findings — not the data itself.
    """

    __tablename__ = "secure_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requested_by: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    content_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    prompt_analysis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_analysis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    masked_findings: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    data_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    generation_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    generation_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    generation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
