from __future__ import annotations

import re

from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)

_EMAIL_PATTERN = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def mask_sensitive_value(value: object, finding_type: AnalysisFindingType) -> str:
    text = str(value)
    if finding_type == AnalysisFindingType.EMAIL:
        return mask_email(text)
    if finding_type == AnalysisFindingType.CREDIT_CARD:
        digits = re.sub(r"\D", "", text)
        return _preserve_edges(digits, 4, 4)
    if finding_type in {
        AnalysisFindingType.PRIVATE_KEY,
    }:
        return "[REDACTED_PRIVATE_KEY]"
    if finding_type == AnalysisFindingType.CVV:
        return "[REDACTED_CVV]"
    if finding_type == AnalysisFindingType.PASSWORD:
        return _preserve_edges(text, 3, 3)
    if finding_type in {
        AnalysisFindingType.API_KEY,
        AnalysisFindingType.AWS_ACCESS_KEY,
    }:
        return _preserve_edges(text, 4, 4)
    if finding_type in {
        AnalysisFindingType.TOKEN,
        AnalysisFindingType.ACCESS_TOKEN,
        AnalysisFindingType.REFRESH_TOKEN,
        AnalysisFindingType.SESSION_ID,
        AnalysisFindingType.SESSION_COOKIE,
    }:
        return _preserve_edges(text, 4, 4)
    if finding_type == AnalysisFindingType.CONNECTION_STRING:
        return _mask_connection_string(text)
    if finding_type in {AnalysisFindingType.PERSONAL_ID, AnalysisFindingType.PASSPORT}:
        return _preserve_edges(text, 1, 2)
    if finding_type == AnalysisFindingType.PHONE:
        return _mask_phone(text)
    if finding_type == AnalysisFindingType.FULL_NAME:
        return " ".join(f"{part[:1]}***" for part in text.split())
    if finding_type == AnalysisFindingType.IP_ADDRESS:
        parts = text.split(".")
        return ".".join([*parts[:-1], "***"]) if len(parts) == 4 else "[MASKED_IP]"
    if finding_type in {
        AnalysisFindingType.BANK_ACCOUNT,
        AnalysisFindingType.FINANCIAL_DATA,
    }:
        return _preserve_edges(text, 2, 2)
    if finding_type == AnalysisFindingType.CARD_EXPIRATION:
        return "[REDACTED_CARD_EXPIRATION]"
    if finding_type == AnalysisFindingType.DEBUG_PAYLOAD:
        return "[REDACTED_DEBUG_PAYLOAD]"
    if finding_type == AnalysisFindingType.PROMPT_INJECTION:
        return "[REDACTED_PROMPT_INJECTION]"
    return _preserve_edges(text, 2, 2)


def mask_email(value: str) -> str:
    match = _EMAIL_PATTERN.fullmatch(value.strip())
    if match is None:
        return _EMAIL_PATTERN.sub(
            lambda item: f"{item.group(1)[:1]}***@{item.group(2)}", value
        )
    return f"{match.group(1)[:1]}***@{match.group(2)}"


def _preserve_edges(value: str, prefix_length: int, suffix_length: int) -> str:
    if not value:
        return "*"
    if len(value) <= prefix_length + suffix_length:
        if len(value) == 1:
            return "*"
        return f"{value[:1]}{'*' * max(1, len(value) - 2)}{value[-1:]}"
    return f"{value[:prefix_length]}{'*' * (len(value) - prefix_length - suffix_length)}{value[-suffix_length:]}"


def _mask_phone(value: str) -> str:
    digit_positions = [
        index for index, character in enumerate(value) if character.isdigit()
    ]
    visible_positions = set(digit_positions[-2:])
    return "".join(
        character if not character.isdigit() or index in visible_positions else "*"
        for index, character in enumerate(value)
    )


def _mask_connection_string(value: str) -> str:
    return re.sub(
        r"(?i)([a-z][a-z0-9+.-]*://[^\s/:]+:)([^\s/@]+)(@)",
        r"\1[REDACTED_PASSWORD]\3",
        value,
    )
