import type { SecurityAnalysis } from '@/contexts/analysis-and-decision/domain/analysis/security-analysis'
import type { SecureInteraction } from '@/contexts/analysis-and-decision/domain/secure-query/secure-interaction'

export interface InteractionPage {
  readonly items: readonly SecureInteraction[]
  readonly page: number
  readonly pageSize: number
  readonly total: number
}

export function totalPages(page: InteractionPage): number {
  return Math.max(1, Math.ceil(page.total / page.pageSize))
}

export interface InteractionRepository {
  list(page: number, pageSize: number, signal?: AbortSignal): Promise<InteractionPage>
  findById(interactionId: number, signal?: AbortSignal): Promise<SecureInteraction>
  findAnalysis(analysisId: number, signal?: AbortSignal): Promise<SecurityAnalysis>
}
