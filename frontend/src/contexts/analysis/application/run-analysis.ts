import type { AnalysisRepository } from '@/contexts/analysis/domain/analysis-repository'

export type AnalysisTarget =
  | { readonly kind: 'prompt'; readonly prompt: string }
  | { readonly kind: 'document'; readonly documentId: number }

export class RunAnalysis {
  private readonly repository: AnalysisRepository
  constructor(repository: AnalysisRepository) { this.repository = repository }

  execute(target: AnalysisTarget, signal?: AbortSignal) {
    if (target.kind === 'prompt') {
      const prompt = target.prompt.trim()
      if (!prompt) throw new Error('Escribe el contenido que quieres revisar.')
      if (prompt.length > 8_000) throw new Error('El contenido no puede superar 8.000 caracteres.')
      return this.repository.analyzePrompt(prompt, signal)
    }
    if (!Number.isInteger(target.documentId) || target.documentId < 1) {
      throw new Error('Escribe un identificador de documento válido.')
    }
    return this.repository.analyzeDocument(target.documentId, signal)
  }
}
