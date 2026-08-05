import type { SecurityAnalysis } from '@/contexts/analysis-and-decision/domain/analysis/security-analysis'
import type { InteractionRepository } from '@/contexts/analysis-and-decision/domain/history/interaction-repository'
import type { SecureInteraction } from '@/contexts/analysis-and-decision/domain/secure-query/secure-interaction'

export interface InteractionDetail {
  readonly interaction: SecureInteraction
  readonly promptAnalysis: SecurityAnalysis | null
  readonly documentAnalysis: SecurityAnalysis | null
}

/**
 * Load one interaction together with the reviews behind it.
 *
 * The underlying reviews are what turn "bloqueada" into an explanation, so a
 * review that cannot be loaded degrades to null instead of failing the whole
 * screen.
 */
export class GetInteraction {
  private readonly repository: InteractionRepository

  constructor(repository: InteractionRepository) {
    this.repository = repository
  }

  async execute(interactionId: number, signal?: AbortSignal): Promise<InteractionDetail> {
    const interaction = await this.repository.findById(interactionId, signal)
    const [promptAnalysis, documentAnalysis] = await Promise.all([
      this.loadAnalysis(interaction.promptAnalysisId, signal),
      this.loadAnalysis(interaction.documentAnalysisId, signal),
    ])
    return { interaction, promptAnalysis, documentAnalysis }
  }

  private async loadAnalysis(
    analysisId: number | null,
    signal?: AbortSignal,
  ): Promise<SecurityAnalysis | null> {
    if (analysisId === null) return null
    try {
      return await this.repository.findAnalysis(analysisId, signal)
    } catch {
      return null
    }
  }
}
