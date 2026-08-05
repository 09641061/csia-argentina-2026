export interface AuthSession {
  readonly accessToken: string
  readonly expiresAt: string
  readonly username: string
}

export function isSessionExpired(session: AuthSession): boolean {
  const expiresAt = Date.parse(session.expiresAt)
  return !Number.isFinite(expiresAt) || expiresAt <= Date.now()
}
