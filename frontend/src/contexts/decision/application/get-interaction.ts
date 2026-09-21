import type { DecisionRepository } from '@/contexts/decision/domain/decision-repository'

export class GetInteraction {
  private readonly repository: DecisionRepository
  constructor(repository: DecisionRepository) { this.repository = repository }
  execute(id: number, signal?: AbortSignal) {
    if (!Number.isInteger(id) || id < 1) throw new Error('La interacción solicitada no es válida.')
    return this.repository.findById(id, signal)
  }
}
