import type { DecisionRepository, SecureQueryDraft } from '@/contexts/decision/domain/decision-repository'
import type { InteractionPage, SecureInteraction, SecureQueryOutcome } from '@/contexts/decision/domain/secure-interaction'
import { request } from '@/shared/infrastructure/api/http-client'
import type { SecureInteractionListResource, SecureInteractionResource, SecureQueryResponseResource } from '@/shared/infrastructure/api/resources'

import { toAssistantAnswer, toSecureInteraction } from './decision-mapper'

export class HttpDecisionRepository implements DecisionRepository {
  async submit(draft: SecureQueryDraft, signal?: AbortSignal): Promise<SecureQueryOutcome> {
    const body = new FormData()
    if (draft.prompt) body.append('prompt', draft.prompt)
    if (draft.file) body.append('file', draft.file, draft.file.name)
    const resource = await request<SecureQueryResponseResource>('/api/v1/secure-queries', { method: 'POST', body, signal })
    return { interaction: toSecureInteraction(resource.interaction), answer: resource.answer ? toAssistantAnswer(resource.answer) : null }
  }

  async list(page: number, pageSize: number, signal?: AbortSignal): Promise<InteractionPage> {
    const resource = await request<SecureInteractionListResource>(`/api/v1/interactions?page=${page}&page_size=${pageSize}`, { signal, timeoutMs: 20_000 })
    return { items: resource.items.map(toSecureInteraction), page: resource.page.page, pageSize: resource.page.page_size, total: resource.page.total }
  }

  async findById(interactionId: number, signal?: AbortSignal): Promise<SecureInteraction> {
    return toSecureInteraction(await request<SecureInteractionResource>(`/api/v1/interactions/${interactionId}`, { signal, timeoutMs: 20_000 }))
  }
}

