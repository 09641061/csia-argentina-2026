import { Spinner } from '@/components/ui/spinner'

interface LoadingStatusProps {
  readonly message: string
}

export function LoadingStatus({ message }: LoadingStatusProps) {
  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground" role="status" aria-live="polite">
      <Spinner aria-hidden="true" />
      {message}
    </div>
  )
}
