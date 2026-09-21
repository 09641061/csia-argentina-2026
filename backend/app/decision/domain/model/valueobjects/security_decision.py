from enum import StrEnum


class SecurityDecision(StrEnum):
    """
    The only two verdicts of the MVP.

    There is deliberately no WARN, no SANITIZE and no REQUIRE_APPROVAL: either
    the content is safe enough to reach the local AI, or it is not.
    """

    ALLOWED = "allowed"
    BLOCKED = "blocked"
