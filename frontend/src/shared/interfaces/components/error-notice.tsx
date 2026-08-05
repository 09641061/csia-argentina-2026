import { AlertCircle } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/shared/interfaces/ui/alert'
import { Button } from '@/shared/interfaces/ui/button'

interface ErrorNoticeProps {
  readonly message: string
  readonly onRetry?: () => void
  readonly retryLabel?: string
}

export function ErrorNotice({ message, onRetry, retryLabel = 'Reintentar' }: ErrorNoticeProps) {
  return (
    <Alert
      className="rounded-2xl border-[#74433a]/60 bg-[#352522] text-[#f5c1b4]"
      role="alert"
    >
      <AlertCircle aria-hidden="true" />
      <AlertTitle>No pudimos completar la operación</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
      {onRetry && (
        <div className="mt-3">
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="border-[#a96352]/50 bg-transparent text-[#ffd8cf] hover:bg-white/[0.06]"
            onClick={onRetry}
          >
            {retryLabel}
          </Button>
        </div>
      )}
    </Alert>
  )
}
