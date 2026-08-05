import type { AssistantResponse } from './assistant-response'
import type { SecureInteraction } from './secure-interaction'
import type { SecureQueryDraft } from './secure-query-draft'

export interface SecureQueryOutcome {
  readonly interaction: SecureInteraction
  readonly answer: AssistantResponse | null
}

export interface SecureQueryRepository {
  submit(draft: SecureQueryDraft, signal?: AbortSignal): Promise<SecureQueryOutcome>
}
