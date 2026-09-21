import type { AuthenticatedUser, AuthRepository } from '@/contexts/iam/domain/auth-repository'

export class GetCurrentUser {
  private readonly repository: AuthRepository

  constructor(repository: AuthRepository) {
    this.repository = repository
  }

  execute(signal?: AbortSignal): Promise<AuthenticatedUser> {
    return this.repository.currentUser(signal)
  }
}
