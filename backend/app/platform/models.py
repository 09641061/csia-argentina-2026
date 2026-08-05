from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.persistence.sqlalchemy.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SecurityPolicyModel(Base):
    __tablename__ = "security_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    mode: Mapped[str] = mapped_column(String(24), nullable=False, default="corporate")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    rules: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    requester: Mapped[str] = mapped_column(String(100), nullable=False, default="Usuario demo")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SanitizationRecordModel(Base):
    __tablename__ = "sanitization_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    safe_content: Mapped[str] = mapped_column(Text, nullable=False)
    replacements: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SecurityEventModel(Base):
    """Privacy-safe SOC event. It stores evidence metadata, never raw content."""

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="observed")
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="usuario-local")
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(48), nullable=False)
    interaction_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    evidence: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class SecurityIncidentModel(Base):
    """Correlated group of events managed by the SOC workflow."""

    __tablename__ = "security_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open", index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="usuario-local")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    rule_id: Mapped[str] = mapped_column(String(48), nullable=False)
    event_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
