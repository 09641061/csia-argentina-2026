import type { AuthRepository } from '@/contexts/iam/domain/auth-repository'
import type { AuthSession } from '@/contexts/iam/domain/auth-session'

export class RegisterUser {
  private readonly repository: AuthRepository

  constructor(repository: AuthRepository) {
    this.repository = repository
  }

  execute(username: string, password: string): Promise<AuthSession> {
    return this.repository.register(username, password)
  }
}
