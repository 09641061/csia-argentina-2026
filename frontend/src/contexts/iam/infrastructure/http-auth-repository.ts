import type { AuthRepository } from '@/contexts/iam/domain/auth-repository'
import type { AuthSession } from '@/contexts/iam/domain/auth-session'
import { request } from '@/shared/infrastructure/api/http-client'
import type { AuthTokenResource, AuthenticatedUserResource } from '@/shared/infrastructure/api/resources'

export class HttpAuthRepository implements AuthRepository {
  async login(username: string, password: string): Promise<AuthSession> {
    const response = await request<AuthTokenResource>('/api/v1/auth/login', {
      method: 'POST',
      body: { username, password },
      authenticated: false,
    })
    return toSession(response)
  }

  async register(username: string, password: string): Promise<AuthSession> {
    const response = await request<AuthTokenResource>('/api/v1/auth/register', {
      method: 'POST',
      body: { username, password },
      authenticated: false,
    })
    return toSession(response)
  }

  async currentUser(signal?: AbortSignal): Promise<AuthenticatedUserResource> {
    return request<AuthenticatedUserResource>('/api/v1/auth/me', { signal })
  }
}

function toSession(resource: AuthTokenResource): AuthSession {
  return {
    accessToken: resource.access_token,
    expiresAt: resource.expires_at,
    username: resource.username,
  }
}
