import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import type { AuthSession } from '@/modules/auth/domain/auth-session'
import {
  AUTH_CHANGED_EVENT,
  clearAuthSession,
  readAuthSession,
  storeAuthSession,
} from '@/modules/auth/infrastructure/auth-storage'
import { HttpAuthRepository } from '@/modules/auth/infrastructure/http-auth-repository'
import { ApiError } from '@/shared/api/api-error'

interface AuthContextValue {
  readonly session: AuthSession | null
  readonly isCheckingSession: boolean
  readonly login: (username: string, password: string) => Promise<void>
  readonly register: (username: string, password: string) => Promise<void>
  readonly logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { readonly children: ReactNode }) {
  const repository = useMemo(() => new HttpAuthRepository(), [])
  const [session, setSession] = useState<AuthSession | null>(() => readAuthSession())
  const [isCheckingSession, setIsCheckingSession] = useState(() => session !== null)

  useEffect(() => {
    const syncSession = () => setSession(readAuthSession())
    window.addEventListener(AUTH_CHANGED_EVENT, syncSession)
    window.addEventListener('storage', syncSession)
    return () => {
      window.removeEventListener(AUTH_CHANGED_EVENT, syncSession)
      window.removeEventListener('storage', syncSession)
    }
  }, [])

  useEffect(() => {
    if (!session) {
      setIsCheckingSession(false)
      return
    }
    const controller = new AbortController()
    setIsCheckingSession(true)
    repository
      .currentUser(controller.signal)
      .then((user) => {
        if (user.username !== session.username) {
          clearAuthSession()
          setSession(null)
        }
      })
      .catch((error: unknown) => {
        if (
          !controller.signal.aborted &&
          error instanceof ApiError &&
          error.kind === 'unauthorized'
        ) {
          clearAuthSession()
          setSession(null)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsCheckingSession(false)
      })
    return () => controller.abort()
  }, [repository, session])

  const persist = useCallback((nextSession: AuthSession) => {
    storeAuthSession(nextSession)
    setSession(nextSession)
  }, [])

  const login = useCallback(
    async (username: string, password: string) => persist(await repository.login(username, password)),
    [persist, repository],
  )

  const register = useCallback(
    async (username: string, password: string) =>
      persist(await repository.register(username, password)),
    [persist, repository],
  )

  const logout = useCallback(() => {
    clearAuthSession()
    setSession(null)
  }, [])

  return (
    <AuthContext.Provider value={{ session, isCheckingSession, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
