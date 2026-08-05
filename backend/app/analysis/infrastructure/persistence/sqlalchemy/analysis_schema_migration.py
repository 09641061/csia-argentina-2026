from __future__ import annotations

from sqlalchemy import JSON, bindparam, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.analysis.application.internal.services.sensitive_value_masking import (
    mask_sensitive_value,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)


async def migrate_analysis_schema(connection: AsyncConnection) -> None:
    """Upgrade only the partial Analytics table without deleting historical rows."""

    if connection.dialect.name != "postgresql":
        return

    statements = (
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS analytics_schema_version INTEGER",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS source_size_bytes INTEGER",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS status VARCHAR(32)",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS secrets_risk VARCHAR(32)",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS personal_data_risk VARCHAR(32)",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS confidence VARCHAR(32)",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS tampering_suspected BOOLEAN",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS data_categories JSON",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS estimated_subjects VARCHAR(32)",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS summary TEXT",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS rationale TEXT",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS sanitized_content JSON",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS content_truncated BOOLEAN",
        "ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS error_message TEXT",
        "ALTER TABLE document_analyses ALTER COLUMN risk_level DROP NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN analyzed_at DROP NOT NULL",
        "ALTER TABLE document_analyses DROP CONSTRAINT IF EXISTS document_analyses_document_id_key",
        "UPDATE document_analyses AS analyses SET source_size_bytes = documents.size_bytes FROM documents WHERE analyses.document_id = documents.id AND analyses.source_size_bytes IS NULL",
        "UPDATE document_analyses SET source_size_bytes = 1 WHERE source_size_bytes IS NULL",
        "UPDATE document_analyses SET explanation = 'Legacy analysis migrated; source evidence was removed. Reanalyze for the expanded result.' WHERE analytics_schema_version IS NULL",
        "UPDATE document_analyses SET status = 'completed' WHERE status IS NULL",
        "UPDATE document_analyses SET secrets_risk = CASE WHEN risk_level = 'low' THEN 'none' ELSE risk_level END WHERE secrets_risk IS NULL",
        "UPDATE document_analyses SET personal_data_risk = COALESCE(risk_level, 'high') WHERE personal_data_risk IS NULL",
        "UPDATE document_analyses SET confidence = 'low' WHERE confidence IS NULL",
        "UPDATE document_analyses SET tampering_suspected = FALSE WHERE tampering_suspected IS NULL",
        "UPDATE document_analyses SET data_categories = '[]'::json WHERE data_categories IS NULL",
        "UPDATE document_analyses SET estimated_subjects = 'unknown' WHERE estimated_subjects IS NULL",
        "UPDATE document_analyses SET summary = 'Legacy analysis migrated; reanalyze for the expanded result.' WHERE summary IS NULL",
        "UPDATE document_analyses SET rationale = 'Historical risk retained; legacy source evidence was removed during the secure migration.' WHERE rationale IS NULL",
        "UPDATE document_analyses SET explanation = summary || ' ' || rationale WHERE explanation IS NULL OR explanation = ''",
        "UPDATE document_analyses SET content_truncated = FALSE WHERE content_truncated IS NULL",
        "UPDATE document_analyses SET analytics_schema_version = 2 WHERE analytics_schema_version IS NULL",
        "ALTER TABLE document_analyses ALTER COLUMN analytics_schema_version SET DEFAULT 2",
        "ALTER TABLE document_analyses ALTER COLUMN analytics_schema_version SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN source_size_bytes SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN status SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN tampering_suspected SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN data_categories SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN estimated_subjects SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN summary SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN rationale SET NOT NULL",
        "ALTER TABLE document_analyses ALTER COLUMN content_truncated SET NOT NULL",
    )
    for statement in statements:
        await connection.execute(text(statement))

    unique_index = await connection.scalar(
        text("""
        SELECT indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'document_analyses'
          AND indexname = 'ix_document_analyses_document_id'
    """)
    )
    if isinstance(unique_index, str) and "UNIQUE INDEX" in unique_index.upper():
        await connection.execute(text("DROP INDEX ix_document_analyses_document_id"))
    await connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_document_analyses_document_id ON document_analyses (document_id)"
        )
    )
    await _sanitize_legacy_findings(connection)


async def _sanitize_legacy_findings(connection: AsyncConnection) -> None:
    rows = await connection.execute(text("SELECT id, findings FROM document_analyses"))
    update_statement = text(
        "UPDATE document_analyses SET findings = :findings WHERE id = :analysis_id"
    ).bindparams(bindparam("findings", type_=JSON))
    for analysis_id, findings in rows:
        if not isinstance(findings, list):
            continue
        changed = False
        safe_findings: list[dict[str, object]] = []
        for index, raw_payload in enumerate(findings, start=1):
            if not isinstance(raw_payload, dict):
                changed = True
                continue
            payload = dict(raw_payload)
            try:
                finding_type = AnalysisFindingType(
                    str(payload.get("finding_type", "other"))
                )
            except ValueError:
                finding_type = AnalysisFindingType.OTHER
            evidence = str(
                payload.pop("evidence", payload.get("masked_evidence", "[REDACTED]"))
            )
            if "*" not in evidence and not evidence.startswith("[REDACTED"):
                evidence = mask_sensitive_value(evidence, finding_type)
            payload.update(
                {
                    "finding_id": str(payload.get("finding_id", f"legacy-f{index}")),
                    "finding_type": finding_type.value,
                    "json_path": str(payload.get("json_path", "$")),
                    "masked_evidence": evidence,
                    "detection_method": str(
                        payload.get("detection_method", "legacy_pattern")
                    ),
                    "confidence": str(payload.get("confidence", "medium")),
                    "occurrences": int(payload.get("occurrences", 1)),
                    "is_placeholder": bool(payload.get("is_placeholder", False)),
                }
            )
            safe_findings.append(payload)
            changed = (
                changed
                or "masked_evidence" not in raw_payload
                or "evidence" in raw_payload
            )
        if changed:
            await connection.execute(
                update_statement,
                {"analysis_id": analysis_id, "findings": safe_findings},
            )
