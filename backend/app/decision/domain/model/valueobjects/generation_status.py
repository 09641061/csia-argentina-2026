from enum import StrEnum


class GenerationStatus(StrEnum):
    """
    Answer generation is tracked separately from the security verdict.

    A content can be ALLOWED and still end with FAILED here, which is a very
    different message for the user than a block.
    """

    NOT_REQUESTED = "not_requested"
    SKIPPED = "skipped"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
