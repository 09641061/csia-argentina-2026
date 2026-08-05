import type { SecurityAnalysis } from '@/modules/analysis/domain/security-analysis'
import { toSecurityAnalysis } from '@/modules/analysis/infrastructure/security-analysis-mapper'
import type {
  InteractionPage,
  InteractionRepository,
} from '@/modules/history/domain/interaction-repository'
import type { SecureInteraction } from '@/modules/secure-query/domain/secure-interaction'
import { toSecureInteraction } from '@/modules/secure-query/infrastructure/secure-interaction-mapper'
import { request } from '@/shared/api/http-client'
import type {
  SecureInteractionListResource,
  SecureInteractionResource,
  SecurityAnalysisResource,
} from '@/shared/api/resources'

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
