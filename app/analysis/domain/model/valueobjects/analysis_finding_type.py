from enum import StrEnum


class AnalysisFindingType(StrEnum):
    EMAIL = "email"
    PASSWORD = "password"
    API_KEY = "api_key"
    TOKEN = "token"
    CREDIT_CARD = "credit_card"
    PRIVATE_KEY = "private_key"
    SECRET = "secret"
    OTHER = "other"

