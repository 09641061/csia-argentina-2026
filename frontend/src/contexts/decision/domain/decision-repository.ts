import type { InteractionPage, SecureInteraction, SecureQueryOutcome } from './secure-interaction'

export interface SecureQueryDraft {
  readonly prompt: string
  readonly file: File | null
}

export interface DecisionRepository {
  submit(draft: SecureQueryDraft, signal?: AbortSignal): Promise<SecureQueryOutcome>
  list(page: number, pageSize: number, signal?: AbortSignal): Promise<InteractionPage>
  findById(interactionId: number, signal?: AbortSignal): Promise<SecureInteraction>
}

