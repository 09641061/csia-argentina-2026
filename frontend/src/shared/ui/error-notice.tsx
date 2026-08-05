interface ErrorNoticeProps {
  readonly message: string
  readonly onRetry?: () => void
  readonly retryLabel?: string
}

export function ErrorNotice({ message, onRetry, retryLabel = 'Reintentar' }: ErrorNoticeProps) {
  return (
    <Alert variant="destructive" role="alert">
      <AlertCircle aria-hidden="true" />
      <AlertTitle>No pudimos completar la operación</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
      {onRetry && (
        <div className="mt-3">
          <Button type="button" size="sm" variant="outline" onClick={onRetry}>
            {retryLabel}
          </Button>
        </div>
      )}
    </Alert>
  )
}
import { AlertCircle } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
