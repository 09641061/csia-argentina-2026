import { createContext, useContext } from 'react'

import type { AuthSession } from '@/contexts/iam/domain/auth-session'

export interface AuthContextValue {
  readonly session: AuthSession | null
  readonly isCheckingSession: boolean
  readonly login: (username: string, password: string) => Promise<void>
  readonly register: (username: string, password: string) => Promise<void>
  readonly logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}

export function useOptionalAuth(): AuthContextValue | null {
  return useContext(AuthContext)
}
