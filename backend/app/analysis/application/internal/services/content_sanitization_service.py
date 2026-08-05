from __future__ import annotations

import re
from collections import defaultdict

from app.analysis.application.internal.services.json_path import append_json_path
from app.analysis.application.internal.services.sensitive_value_masking import (
    mask_email,
    mask_sensitive_value,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)
from app.analysis.domain.model.valueobjects.json_types import JsonContainer, JsonValue

_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_REPLACEMENTS = {
    AnalysisFindingType.PASSWORD: "[REDACTED_PASSWORD]",
    AnalysisFindingType.API_KEY: "[REDACTED_API_KEY]",
    AnalysisFindingType.AWS_ACCESS_KEY: "[REDACTED_API_KEY]",
    AnalysisFindingType.TOKEN: "[REDACTED_TOKEN]",
    AnalysisFindingType.ACCESS_TOKEN: "[REDACTED_TOKEN]",
    AnalysisFindingType.REFRESH_TOKEN: "[REDACTED_TOKEN]",
    AnalysisFindingType.SESSION_ID: "[REDACTED_TOKEN]",
    AnalysisFindingType.SESSION_COOKIE: "[REDACTED_TOKEN]",
    AnalysisFindingType.CONNECTION_STRING: "[REDACTED_CONNECTION_STRING]",
    AnalysisFindingType.CREDIT_CARD: "[REDACTED_CARD]",
    AnalysisFindingType.CVV: "[REDACTED_CVV]",
    AnalysisFindingType.CARD_EXPIRATION: "[REDACTED_CARD_EXPIRATION]",
    AnalysisFindingType.PRIVATE_KEY: "[REDACTED_PRIVATE_KEY]",
    AnalysisFindingType.DEBUG_PAYLOAD: "[REDACTED_DEBUG_PAYLOAD]",
    AnalysisFindingType.PROMPT_INJECTION: "[REDACTED_PROMPT_INJECTION]",
}
_PRIORITY = (
    AnalysisFindingType.DEBUG_PAYLOAD,
    AnalysisFindingType.PRIVATE_KEY,
    AnalysisFindingType.CONNECTION_STRING,
    AnalysisFindingType.PASSWORD,
    AnalysisFindingType.API_KEY,
    AnalysisFindingType.AWS_ACCESS_KEY,
    AnalysisFindingType.ACCESS_TOKEN,
    AnalysisFindingType.REFRESH_TOKEN,
    AnalysisFindingType.TOKEN,
    AnalysisFindingType.SESSION_COOKIE,
    AnalysisFindingType.SESSION_ID,
    AnalysisFindingType.CREDIT_CARD,
    AnalysisFindingType.CVV,
    AnalysisFindingType.CARD_EXPIRATION,
    AnalysisFindingType.PROMPT_INJECTION,
    AnalysisFindingType.BANK_ACCOUNT,
    AnalysisFindingType.PERSONAL_ID,
    AnalysisFindingType.PASSPORT,
    AnalysisFindingType.PHONE,
    AnalysisFindingType.EMAIL,
    AnalysisFindingType.FULL_NAME,
    AnalysisFindingType.IP_ADDRESS,
    AnalysisFindingType.FINANCIAL_DATA,
)


class ContentSanitizationService:
    def sanitize(
        self,
        content: JsonContainer,
        findings: list[AnalysisFinding],
    ) -> JsonContainer:
        findings_by_path: dict[str, set[AnalysisFindingType]] = defaultdict(set)
        for finding in findings:
            findings_by_path[finding.json_path].add(finding.finding_type)
        sanitized = self._sanitize_value(content, "$", findings_by_path)
        if not isinstance(sanitized, (dict, list)):
            raise TypeError("Sanitized JSON root must remain an object or array")
        return sanitized

    def _sanitize_value(
        self,
        value: JsonValue,
        path: str,
        findings_by_path: dict[str, set[AnalysisFindingType]],
    ) -> JsonValue:
        finding_types = findings_by_path.get(path, set())
        for finding_type in _PRIORITY:
            if finding_type not in finding_types:
                continue
            if finding_type in _REPLACEMENTS:
                return _REPLACEMENTS[finding_type]
            if not isinstance(value, (dict, list)):
                return mask_sensitive_value(value, finding_type)

        if isinstance(value, dict):
            return {
                key: self._sanitize_value(
                    child, append_json_path(path, key), findings_by_path
                )
                for key, child in value.items()
            }
        if isinstance(value, list):
            return [
                self._sanitize_value(
                    child, append_json_path(path, index), findings_by_path
                )
                for index, child in enumerate(value)
            ]
        if isinstance(value, str):
            return _EMAIL_PATTERN.sub(lambda match: mask_email(match.group(0)), value)
        return value
