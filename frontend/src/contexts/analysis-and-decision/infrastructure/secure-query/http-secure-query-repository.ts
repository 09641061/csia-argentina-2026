import type {
  SecureQueryOutcome,
  SecureQueryRepository,
} from '@/contexts/analysis-and-decision/domain/secure-query/secure-query-repository'
import type { SecureQueryDraft } from '@/contexts/analysis-and-decision/domain/secure-query/secure-query-draft'
import { request } from '@/shared/infrastructure/api/http-client'
import type { SecureQueryResponseResource } from '@/shared/infrastructure/api/resources'

import { toAssistantResponse, toSecureInteraction } from './secure-interaction-mapper'

export class HttpSecureQueryRepository implements SecureQueryRepository {
  async submit(draft: SecureQueryDraft, signal?: AbortSignal): Promise<SecureQueryOutcome> {
    const body = new FormData()
    if (draft.prompt.trim()) body.append('prompt', draft.prompt.trim())
    if (draft.document) body.append('file', draft.document, draft.document.name)

    const response = await request<SecureQueryResponseResource>('/api/v1/secure-queries', {
      method: 'POST',
      body,
      signal,
    })

    return {
      interaction: toSecureInteraction(response.interaction),
      answer: response.answer ? toAssistantResponse(response.answer) : null,
    }
  }
}
