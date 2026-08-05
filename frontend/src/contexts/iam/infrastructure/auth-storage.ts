import { isSessionExpired, type AuthSession } from '@/contexts/iam/domain/auth-session'

const STORAGE_KEY = 'sentinel.auth.session'
export const AUTH_CHANGED_EVENT = 'sentinel:auth-changed'

export function readAuthSession(): AuthSession | null {
  try {
    const serialized = window.localStorage.getItem(STORAGE_KEY)
    if (!serialized) return null
    const parsed = JSON.parse(serialized) as Partial<AuthSession>
    if (
      typeof parsed.accessToken !== 'string' ||
      typeof parsed.expiresAt !== 'string' ||
      typeof parsed.username !== 'string'
    ) {
      clearAuthSession()
      return null
    }
    const session: AuthSession = {
      accessToken: parsed.accessToken,
      expiresAt: parsed.expiresAt,
      username: parsed.username,
    }
    if (isSessionExpired(session)) {
      clearAuthSession()
      return null
    }
    return session
  } catch {
    clearAuthSession()
    return null
  }
}

export function storeAuthSession(session: AuthSession): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  notifyAuthChanged()
}

export function clearAuthSession(): void {
  window.localStorage.removeItem(STORAGE_KEY)
}

export function currentAccessToken(): string | null {
  return readAuthSession()?.accessToken ?? null
}

export function notifyAuthChanged(): void {
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT))
}
