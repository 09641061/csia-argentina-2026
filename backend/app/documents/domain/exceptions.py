class DocumentDomainError(ValueError):
    pass


class DocumentNotFoundError(DocumentDomainError):
    pass


class UnsupportedDocumentTypeError(DocumentDomainError):
    pass


class DocumentFileTooLargeError(DocumentDomainError):
    pass


class InvalidDocumentContentError(DocumentDomainError):
    pass

