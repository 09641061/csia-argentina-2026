class DocumentStorageError(RuntimeError):
    pass


class DocumentStorageUploadError(DocumentStorageError):
    pass


class DocumentStorageReadError(DocumentStorageError):
    pass


class DocumentStorageNotConfiguredError(DocumentStorageError):
    pass
