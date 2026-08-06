import type { AnalysisRepository } from '@/contexts/analysis/domain/analysis-repository'

export class ListAnalyses {
  private readonly repository: AnalysisRepository
  constructor(repository: AnalysisRepository) { this.repository = repository }

  execute(page: number, signal?: AbortSignal) {
    const safePage = Number.isInteger(page) && page > 0 ? page : 1
    return this.repository.list(safePage, 12, signal)
  }
}
