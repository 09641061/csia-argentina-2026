class AnalysisDomainError(ValueError):
    pass


class AnalysisNotFoundError(AnalysisDomainError):
    pass


class DocumentSourceNotFoundError(AnalysisDomainError):
    pass


class DocumentContentExtractionError(AnalysisDomainError):
    pass


class DocumentContentReadError(AnalysisDomainError):
    pass


class InvalidPromptError(AnalysisDomainError):
    pass


class AnalysisModelError(AnalysisDomainError):
    pass


class AnalysisModelUnavailableError(AnalysisModelError):
    pass


class AnalysisModelTimeoutError(AnalysisModelError):
    pass


class AnalysisModelInvalidResponseError(AnalysisModelError):
    pass


class AnalysisExecutionError(AnalysisDomainError):
    """An unexpected failure that was already recorded as a failed execution."""
