import { Spinner } from '@/shared/interfaces/ui/spinner'

interface LoadingStatusProps {
  readonly message: string
}

export function LoadingStatus({ message }: LoadingStatusProps) {
  return (
    <div
      className="flex items-center justify-center gap-3 rounded-2xl border border-white/[0.06] bg-[#242422] px-4 py-3 text-sm text-[#aaa89f]"
      role="status"
      aria-live="polite"
    >
      <Spinner className="text-[#d97757]" aria-hidden="true" />
      {message}
    </div>
  )
}
