import {
  canSubmit,
  draftProblem,
  draftProblemMessage,
  type SecureQueryDraft,
} from '@/modules/secure-query/domain/secure-query-draft'
import type {
  SecureQueryOutcome,
  SecureQueryRepository,
} from '@/modules/secure-query/domain/secure-query-repository'
import { ApiError } from '@/shared/api/api-error'

/**
 * Send one secure query.
 *
 * The only checks performed here are the ones the user can fix before sending.
 * Whether the content is safe is decided by the backend and simply reported.
 */
export class SubmitSecureQuery {
  private readonly repository: SecureQueryRepository

  constructor(repository: SecureQueryRepository) {
    this.repository = repository
  }

  async execute(draft: SecureQueryDraft, signal?: AbortSignal): Promise<SecureQueryOutcome> {
    if (!canSubmit(draft)) {
      const problem = draftProblem(draft)
      throw new ApiError('bad_request', draftProblemMessage(problem ?? 'empty'))
    }
    return this.repository.submit(draft, signal)
  }
}
