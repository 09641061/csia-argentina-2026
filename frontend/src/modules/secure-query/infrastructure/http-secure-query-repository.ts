import type {
  SecureQueryOutcome,
  SecureQueryRepository,
} from '@/modules/secure-query/domain/secure-query-repository'
import type { SecureQueryDraft } from '@/modules/secure-query/domain/secure-query-draft'
import { request } from '@/shared/api/http-client'
import type { SecureQueryResponseResource } from '@/shared/api/resources'

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
