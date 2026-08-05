from enum import StrEnum


class EstimatedSubjects(StrEnum):
    ZERO = "0"
    ONE_TO_FIVE = "1-5"
    SIX_TO_ONE_HUNDRED = "6-100"
    OVER_ONE_HUNDRED = "100+"
    UNKNOWN = "unknown"
