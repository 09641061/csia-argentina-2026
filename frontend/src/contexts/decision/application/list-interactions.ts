import type { DecisionRepository } from '@/contexts/decision/domain/decision-repository'

export class ListInteractions {
  private readonly repository: DecisionRepository
  constructor(repository: DecisionRepository) { this.repository = repository }
  execute(page: number, signal?: AbortSignal) { return this.repository.list(page > 0 ? page : 1, 15, signal) }
}
