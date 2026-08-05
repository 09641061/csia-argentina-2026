class DecisionDomainError(ValueError):
    pass


class SecureQueryValidationError(DecisionDomainError):
    pass


class SecureInteractionNotFoundError(DecisionDomainError):
    pass


class AnswerGenerationError(DecisionDomainError):
    pass


class AnswerGenerationUnavailableError(AnswerGenerationError):
    pass


class AnswerGenerationTimeoutError(AnswerGenerationError):
    pass


class AnswerGenerationEmptyError(AnswerGenerationError):
    pass


class AnswerGenerationContextTooLargeError(AnswerGenerationError):
    pass
