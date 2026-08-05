import type { SecurityAnalysis } from '@/contexts/analysis-and-decision/domain/analysis/security-analysis'
import { toSecurityAnalysis } from '@/contexts/analysis-and-decision/infrastructure/analysis/security-analysis-mapper'
import type {
  InteractionPage,
  InteractionRepository,
} from '@/contexts/analysis-and-decision/domain/history/interaction-repository'
import type { SecureInteraction } from '@/contexts/analysis-and-decision/domain/secure-query/secure-interaction'
import { toSecureInteraction } from '@/contexts/analysis-and-decision/infrastructure/secure-query/secure-interaction-mapper'
import { request } from '@/shared/infrastructure/api/http-client'
import type {
  SecureInteractionListResource,
  SecureInteractionResource,
  SecurityAnalysisResource,
} from '@/shared/infrastructure/api/resources'

export class HttpInteractionRepository implements InteractionRepository {
  async list(page: number, pageSize: number, signal?: AbortSignal): Promise<InteractionPage> {
    const response = await request<SecureInteractionListResource>(
      `/api/v1/interactions?page=${page}&page_size=${pageSize}`,
      { signal, timeoutMs: 20_000 },
    )
    return {
      items: response.items.map(toSecureInteraction),
      page: response.page.page,
      pageSize: response.page.page_size,
      total: response.page.total,
    }
  }

  async findById(interactionId: number, signal?: AbortSignal): Promise<SecureInteraction> {
    const response = await request<SecureInteractionResource>(
      `/api/v1/interactions/${interactionId}`,
      { signal, timeoutMs: 20_000 },
    )
    return toSecureInteraction(response)
  }

  async findAnalysis(analysisId: number, signal?: AbortSignal): Promise<SecurityAnalysis> {
    const response = await request<SecurityAnalysisResource>(`/api/v1/analyses/${analysisId}`, {
      signal,
      timeoutMs: 20_000,
    })
    return toSecurityAnalysis(response)
  }
}
