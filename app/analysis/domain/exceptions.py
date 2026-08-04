class AnalysisDomainError(ValueError):
    pass


class AnalysisNotFoundError(AnalysisDomainError):
    pass


class DocumentSourceNotFoundError(AnalysisDomainError):
    pass


class DocumentContentExtractionError(AnalysisDomainError):
    pass


class AnalysisModelUnavailableError(AnalysisDomainError):
    pass

