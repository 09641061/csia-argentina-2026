from __future__ import annotations

import re

_EMAIL_PATTERN = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_AWS_ACCESS_KEY_PATTERN = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
_KNOWN_TOKEN_PATTERN = re.compile(
    r"(?i)\b(?:sk-(?:live|test|proj)|gh[opusr]_|xox[baprs]-|SG\.|hvs\.)[A-Za-z0-9_./+=-]{8,}"
)
_CONNECTION_STRING_PATTERN = re.compile(
    r"(?i)\b([a-z][a-z0-9+.-]*://[^\s/:]+:)([^\s/@]+)(@)"
)
_LABELED_SECRET_PATTERN = re.compile(
    r"(?i)\b(password|passwd|pwd|contrase(?:n|ñ)a|clave|api[_\- ]?key|secret|"
    r"access[_\- ]?token|refresh[_\- ]?token|token|bearer)\b\s*(?:[:=]|\bes\b|\bis\b)\s*"
    r"([^\s,;\"']{3,})"
)
_LONG_DIGITS_PATTERN = re.compile(r"(?<!\d)(?:\d[ \-]?){7,19}(?!\d)")
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----[\s\S]*?"
    r"(?:-----END (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----)?",
    re.IGNORECASE,
)


def mask_free_text(value: str) -> str:
    """
    Mask credential-shaped and identity-shaped substrings inside free text.

    Used for anything that leaves the trusted boundary as plain text: filenames,
    prompt previews, JSON keys and JSONPaths sent to the security model, and any
    audit trail. It is deliberately aggressive: over-masking is safe, leaking is
    not.
    """

    if not value:
        return value

    masked = _PRIVATE_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", value)
    masked = _CONNECTION_STRING_PATTERN.sub(r"\1[REDACTED_PASSWORD]\3", masked)
    masked = _AWS_ACCESS_KEY_PATTERN.sub(
        lambda match: preserve_edges(match.group(0), 4, 4), masked
    )
    masked = _KNOWN_TOKEN_PATTERN.sub(
        lambda match: preserve_edges(match.group(0), 4, 4), masked
    )
    masked = _LABELED_SECRET_PATTERN.sub(
        lambda match: f"{match.group(1)}: [REDACTED_SECRET]", masked
    )
    masked = _EMAIL_PATTERN.sub(
        lambda match: f"{match.group(1)[:1]}***@{match.group(2)}", masked
    )
    masked = _LONG_DIGITS_PATTERN.sub(
        lambda match: preserve_edges(match.group(0), 0, 2), masked
    )
    return masked


def preserve_edges(value: str, prefix_length: int, suffix_length: int) -> str:
    if not value:
        return "*"
    if len(value) <= prefix_length + suffix_length:
        if len(value) == 1:
            return "*"
        return f"{value[:1]}{'*' * max(1, len(value) - 2)}{value[-1:]}"
    hidden = "*" * (len(value) - prefix_length - suffix_length)
    suffix = value[-suffix_length:] if suffix_length else ""
    return f"{value[:prefix_length]}{hidden}{suffix}"


def contains_sensitive_shape(value: str) -> bool:
    """Report whether free text carries a credential-shaped or identity-shaped substring."""

    return mask_free_text(value) != value
