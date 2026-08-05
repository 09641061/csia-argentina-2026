from enum import StrEnum


class EstimatedSubjects(StrEnum):
    ZERO = "0"
    ONE_TO_FIVE = "1-5"
    SIX_TO_ONE_HUNDRED = "6-100"
    OVER_ONE_HUNDRED = "100+"
    UNKNOWN = "unknown"

    @classmethod
    def from_model_answer(cls, value: str) -> "EstimatedSubjects":
        """
        Read a bucket, accepting the plain count a model sometimes writes instead.

        Asked for one of `0`, `1-5`, `6-100`, `100+`, the local model answers
        `"1"` often enough to matter, and rejecting that failed the whole review
        — which the policy reads as BLOCKED. A stated count carries the same
        information as its bucket, so it is placed in the bucket it falls into
        rather than thrown away. Anything else still raises.
        """

        normalized = value.strip()
        try:
            return cls(normalized)
        except ValueError:
            pass
        if not normalized.isdigit():
            raise ValueError(f"'{value}' is not a valid EstimatedSubjects")
        count = int(normalized)
        if count == 0:
            return cls.ZERO
        if count <= 5:
            return cls.ONE_TO_FIVE
        if count <= 100:
            return cls.SIX_TO_ONE_HUNDRED
        return cls.OVER_ONE_HUNDRED
