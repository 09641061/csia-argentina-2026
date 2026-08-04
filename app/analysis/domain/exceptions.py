class AnalysisDomainError(ValueError):
    pass


class AnalysisNotFoundError(AnalysisDomainError):
    pass


class DocumentSourceNotFoundError(AnalysisDomainError):
    pass


class DocumentContentExtractionError(AnalysisDomainError):
    pass


class DocumentContentDownloadError(AnalysisDomainError):
    pass


class AnalysisConflictError(AnalysisDomainError):
    pass


class AnalysisModelError(AnalysisDomainError):
    pass


class AnalysisModelUnavailableError(AnalysisModelError):
    pass


class AnalysisModelTimeoutError(AnalysisModelError):
    pass


class AnalysisModelInvalidResponseError(AnalysisModelError):
    pass
