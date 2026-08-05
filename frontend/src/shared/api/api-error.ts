export type ApiErrorKind =
  | 'offline'
  | 'timeout'
  | 'bad_request'
  | 'not_found'
  | 'too_large'
  | 'unsupported_media'
  | 'server'
  | 'unknown'

/**
 * A failure translated into something a non-technical person can act on.
 *
 * The backend already refuses to send stack traces or internal paths; this type
 * makes sure nothing raw reaches the screen even if a proxy or the browser
 * produces the failure instead.
 */
export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null

  constructor(kind: ApiErrorKind, message: string, status: number | null = null) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
  }

  get isRetryable(): boolean {
    return this.kind === 'offline' || this.kind === 'timeout' || this.kind === 'server'
  }
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Ocurrió un problema inesperado. Vuelve a intentarlo.'
}

export function isRetryable(error: unknown): boolean {
  return error instanceof ApiError && error.isRetryable
}
