import type { AnalysisRepository } from '@/contexts/analysis/domain/analysis-repository'

export class GetAnalysisDetail {
  private readonly repository: AnalysisRepository
  constructor(repository: AnalysisRepository) { this.repository = repository }

  async execute(analysisId: number, signal?: AbortSignal) {
    if (!Number.isInteger(analysisId) || analysisId < 1) throw new Error('El análisis solicitado no es válido.')
    const [analysis, findings] = await Promise.all([
      this.repository.findById(analysisId, signal),
      this.repository.listFindings(analysisId, signal),
    ])
    return { analysis: { ...analysis, findings } }
  }
}
