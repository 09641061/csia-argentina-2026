import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { AuthenticateUser } from '@/contexts/iam/application/authenticate-user'
import { GetCurrentUser } from '@/contexts/iam/application/get-current-user'
import { RegisterUser } from '@/contexts/iam/application/register-user'
import type { AuthSession } from '@/contexts/iam/domain/auth-session'
import {
  AUTH_CHANGED_EVENT,
  clearAuthSession,
  readAuthSession,
  storeAuthSession,
} from '@/contexts/iam/infrastructure/auth-storage'
import { HttpAuthRepository } from '@/contexts/iam/infrastructure/http-auth-repository'
import { ApiError } from '@/shared/infrastructure/api/api-error'
import { AuthContext } from '@/contexts/iam/interfaces/auth-context'

export function AuthProvider({ children }: { readonly children: ReactNode }) {
  const repository = useMemo(() => new HttpAuthRepository(), [])
  const authenticateUser = useMemo(() => new AuthenticateUser(repository), [repository])
  const registerUser = useMemo(() => new RegisterUser(repository), [repository])
  const getCurrentUser = useMemo(() => new GetCurrentUser(repository), [repository])
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
    getCurrentUser
      .execute(controller.signal)
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
  }, [getCurrentUser, session])

  const persist = useCallback((nextSession: AuthSession) => {
    storeAuthSession(nextSession)
    setSession(nextSession)
  }, [])

  const login = useCallback(
    async (username: string, password: string) =>
      persist(await authenticateUser.execute(username, password)),
    [authenticateUser, persist],
  )

  const register = useCallback(
    async (username: string, password: string) =>
      persist(await registerUser.execute(username, password)),
    [persist, registerUser],
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
