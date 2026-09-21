import type { AuthSession } from './auth-session'

export interface AuthenticatedUser {
  readonly username: string
}

export interface AuthRepository {
  login(username: string, password: string): Promise<AuthSession>
  register(username: string, password: string): Promise<AuthSession>
  currentUser(signal?: AbortSignal): Promise<AuthenticatedUser>
}
