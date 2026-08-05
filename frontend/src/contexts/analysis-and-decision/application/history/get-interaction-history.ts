import type {
  InteractionPage,
  InteractionRepository,
} from '@/contexts/analysis-and-decision/domain/history/interaction-repository'

export const HISTORY_PAGE_SIZE = 10

export class GetInteractionHistory {
  private readonly repository: InteractionRepository

  constructor(repository: InteractionRepository) {
    this.repository = repository
  }

  execute(page: number, signal?: AbortSignal): Promise<InteractionPage> {
    const safePage = Number.isFinite(page) && page >= 1 ? Math.floor(page) : 1
    return this.repository.list(safePage, HISTORY_PAGE_SIZE, signal)
  }
}
