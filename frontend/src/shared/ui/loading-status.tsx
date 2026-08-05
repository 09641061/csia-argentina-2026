interface LoadingStatusProps {
  readonly message: string
}

export function LoadingStatus({ message }: LoadingStatusProps) {
  return (
    <p className="status" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      {message}
    </p>
  )
}
