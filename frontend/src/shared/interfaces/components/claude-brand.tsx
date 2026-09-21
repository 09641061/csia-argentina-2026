import { cn } from '@/shared/interfaces/utils'

interface BrandAssetProps {
  readonly className?: string
}

export function ClaudeWordmark({ className }: BrandAssetProps) {
  return (
    <img
      src="/brand/claude-logo-ivory.svg"
      alt="Claude"
      className={cn('block h-auto w-24', className)}
    />
  )
}

export function ClaudeSpark({ className }: BrandAssetProps) {
  return (
    <img
      src="/brand/claude-spark-clay.svg"
      alt=""
      aria-hidden="true"
      className={cn('block size-10', className)}
    />
  )
}

export function ClaudeIcon({ className }: BrandAssetProps) {
  return (
    <img
      src="/brand/claude-icon-rounded.svg"
      alt=""
      aria-hidden="true"
      className={cn('block size-9 rounded-[0.6rem]', className)}
    />
  )
}
