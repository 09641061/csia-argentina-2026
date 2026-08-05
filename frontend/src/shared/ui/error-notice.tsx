interface ErrorNoticeProps {
  readonly message: string
  readonly onRetry?: () => void
  readonly retryLabel?: string
}

export function ErrorNotice({ message, onRetry, retryLabel = 'Reintentar' }: ErrorNoticeProps) {
  return (
    <div className="notice notice--error" role="alert">
      <p>{message}</p>
      {onRetry && (
        <p className="notice__actions">
          <button type="button" className="button button--secondary" onClick={onRetry}>
            {retryLabel}
          </button>
        </p>
      )}
    </div>
  )
}
