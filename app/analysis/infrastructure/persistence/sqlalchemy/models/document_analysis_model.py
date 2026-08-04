from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.documents.infrastructure.persistence.sqlalchemy.models.base import Base


class DocumentAnalysisModel(Base):
    __tablename__ = "document_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analytics_schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, server_default="2"
    )
    document_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    source_document_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    risk_level: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    secrets_risk: Mapped[str | None] = mapped_column(String(32), nullable=True)
    personal_data_risk: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tampering_suspected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    data_categories: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    estimated_subjects: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    findings: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    sanitized_content: Mapped[dict[str, object] | list[object] | None] = mapped_column(
        JSON, nullable=True
    )
    content_truncated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
