from enum import StrEnum


class DecisionReasonCode(StrEnum):
    """Machine-readable explanation of why an interaction was allowed or blocked."""

    CONTENT_IS_SAFE = "content_is_safe"
    NO_CONTENT_SUBMITTED = "no_content_submitted"
    PROMPT_CONTAINS_SENSITIVE_DATA = "prompt_contains_sensitive_data"
    DOCUMENT_CONTAINS_SENSITIVE_DATA = "document_contains_sensitive_data"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    PROMPT_REVIEW_FAILED = "prompt_review_failed"
    DOCUMENT_REVIEW_FAILED = "document_review_failed"
