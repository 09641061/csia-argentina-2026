import type { ContentType } from '@/modules/analysis/domain/content-type'
import type { Decision } from '@/modules/analysis/domain/decision'
import type { Finding } from '@/modules/analysis/domain/finding'
import type { GenerationStatus } from '@/modules/analysis/domain/generation-status'
import type { RiskLevel } from '@/modules/analysis/domain/risk-level'

/**
 * One audited secure query.
 *
 * The decision belongs to the backend. Nothing on this side recomputes it; the
 * UI only renders what was decided and why.
 */
export interface SecureInteraction {
  readonly id: number
  readonly contentType: ContentType
  readonly decision: Decision
  readonly reasonCode: string
  readonly reason: string
  readonly contentReference: string
  readonly riskLevel: RiskLevel | null
  readonly promptAnalysisId: number | null
  readonly documentAnalysisId: number | null
  readonly documentId: number | null
  readonly dataCategories: readonly string[]
  readonly maskedFindings: readonly Finding[]
  readonly generationStatus: GenerationStatus
  readonly generationModel: string | null
  readonly generationError: string | null
  readonly generatedAt: string | null
  readonly createdAt: string
}

export function wasAllowed(interaction: SecureInteraction): boolean {
  return interaction.decision === 'allowed'
}

/**
 * True when the content passed the review but no answer could be produced.
 *
 * This case deserves its own message: the user did nothing wrong, the local
 * assistant simply failed.
 */
export function passedReviewButHasNoAnswer(interaction: SecureInteraction): boolean {
  return wasAllowed(interaction) && interaction.generationStatus === 'failed'
}
