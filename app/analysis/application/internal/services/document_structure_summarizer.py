from __future__ import annotations

import hashlib
import json
from collections import Counter

from app.analysis.application.internal.services.json_path import append_json_path
from app.analysis.application.internal.services.sensitive_data_detection_service import (
    SensitiveDataDetectionService,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)
from app.analysis.domain.model.valueobjects.document_structure_summary import (
    DocumentStructureSummary,
)
from app.analysis.domain.model.valueobjects.estimated_subjects import EstimatedSubjects
from app.analysis.domain.model.valueobjects.json_types import JsonContainer, JsonValue

_SUBJECT_FIELDS = {
    "email",
    "customer_email",
    "user_email",
    "phone",
    "mobile",
    "telefono",
    "document_number",
    "dni",
    "national_id",
    "passport_number",
    "full_name",
    "customer_name",
}


class DocumentStructureSummarizer:
    def summarize(
        self,
        *,
        content: JsonContainer,
        sanitized_content: JsonContainer,
        findings: list[AnalysisFinding],
        approximate_size_bytes: int,
    ) -> DocumentStructureSummary:
        key_counts: Counter[str] = Counter()
        safe_leaves: list[str] = []
        counts = {"objects": 0, "arrays": 0, "scalars": 0, "records": 0}
        self._collect_structure(sanitized_content, "$", key_counts, safe_leaves, counts)
        estimated_subjects = self._estimate_subjects(content, findings)
        finding_counts = Counter(finding.finding_type.value for finding in findings)
        categories = sorted(
            {finding.data_category for finding in findings if finding.data_category}
        )
        injection_paths = tuple(
            finding.json_path
            for finding in findings
            if finding.finding_type == AnalysisFindingType.PROMPT_INJECTION
        )
        truncated = len(safe_leaves) > 50 or approximate_size_bytes > 6000
        return DocumentStructureSummary(
            root_type="object" if isinstance(content, dict) else "array",
            approximate_size_bytes=approximate_size_bytes,
            object_count=counts["objects"],
            array_count=counts["arrays"],
            scalar_count=counts["scalars"],
            record_count=counts["records"],
            top_keys=tuple(key for key, _ in key_counts.most_common(20)),
            finding_counts=tuple(sorted(finding_counts.items())),
            data_categories=tuple(categories),
            estimated_subjects=estimated_subjects,
            safe_sample=self._sample_across_document(safe_leaves),
            truncated=truncated,
            prompt_injection_paths=injection_paths,
        )

    def _collect_structure(
        self,
        value: JsonValue,
        path: str,
        key_counts: Counter[str],
        safe_leaves: list[str],
        counts: dict[str, int],
    ) -> None:
        if isinstance(value, dict):
            counts["objects"] += 1
            for key, child in value.items():
                key_counts[key] += 1
                self._collect_structure(
                    child, append_json_path(path, key), key_counts, safe_leaves, counts
                )
            return
        if isinstance(value, list):
            counts["arrays"] += 1
            if value and all(isinstance(item, dict) for item in value):
                counts["records"] = max(counts["records"], len(value))
            for index, child in enumerate(value):
                self._collect_structure(
                    child,
                    append_json_path(path, index),
                    key_counts,
                    safe_leaves,
                    counts,
                )
            return
        counts["scalars"] += 1
        rendered = json.dumps(value, ensure_ascii=False)
        safe_leaves.append(f"{path}={rendered[:180]}")

    def _estimate_subjects(
        self,
        content: JsonContainer,
        findings: list[AnalysisFinding],
    ) -> EstimatedSubjects:
        fingerprints: set[str] = set()

        def visit(value: JsonValue) -> None:
            if isinstance(value, dict):
                identifiers: list[str] = []
                for key, child in value.items():
                    normalized = SensitiveDataDetectionService.normalize_field_name(key)
                    if normalized in _SUBJECT_FIELDS and isinstance(child, (str, int)):
                        digest = hashlib.sha256(
                            str(child).strip().lower().encode("utf-8")
                        ).hexdigest()
                        identifiers.append(digest)
                    visit(child)
                if identifiers:
                    fingerprints.add(identifiers[0])
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(content)
        personal_types = {
            AnalysisFindingType.EMAIL,
            AnalysisFindingType.FULL_NAME,
            AnalysisFindingType.PHONE,
            AnalysisFindingType.PERSONAL_ID,
            AnalysisFindingType.PASSPORT,
            AnalysisFindingType.CREDIT_CARD,
            AnalysisFindingType.BANK_ACCOUNT,
        }
        if not fingerprints and any(
            finding.finding_type in personal_types for finding in findings
        ):
            count = 1
        else:
            count = len(fingerprints)
        if count == 0:
            return EstimatedSubjects.ZERO
        if count <= 5:
            return EstimatedSubjects.ONE_TO_FIVE
        if count <= 100:
            return EstimatedSubjects.SIX_TO_ONE_HUNDRED
        return EstimatedSubjects.OVER_ONE_HUNDRED

    def _sample_across_document(self, safe_leaves: list[str]) -> tuple[str, ...]:
        if len(safe_leaves) <= 12:
            return tuple(safe_leaves)
        indices = list(range(4))
        midpoint = len(safe_leaves) // 2
        indices.extend(
            range(max(4, midpoint - 2), min(len(safe_leaves) - 4, midpoint + 2))
        )
        indices.extend(range(len(safe_leaves) - 4, len(safe_leaves)))
        return tuple(safe_leaves[index] for index in dict.fromkeys(indices))
