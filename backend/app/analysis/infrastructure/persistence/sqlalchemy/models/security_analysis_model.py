from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.persistence.sqlalchemy.base import Base


class SecurityAnalysisModel(Base):
    """
    Stored security review.

    There is no column for the original prompt, the original document or a
    sanitized copy: only a fingerprint, a masked preview and masked findings are
    kept, which is what makes the audit trail safe to browse.
    """

    __tablename__ = "security_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    content_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    masked_preview: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    secrets_risk: Mapped[str | None] = mapped_column(String(32), nullable=True)
    personal_data_risk: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tampering_suspected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    estimated_subjects: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    findings: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    content_truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
