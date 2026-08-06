export type Decision = 'allowed' | 'blocked'
export type GenerationStatus = 'not_requested' | 'skipped' | 'succeeded' | 'failed'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export interface MaskedFinding {
  readonly origin: 'prompt' | 'document'
  readonly findingType: string
  readonly severity: RiskLevel
  readonly title: string
  readonly location: string
  readonly maskedEvidence: string
  readonly occurrences: number
  readonly isPlaceholder: boolean
}

export interface SecureInteraction {
  readonly id: number
  readonly contentType: 'prompt' | 'document' | 'prompt_with_document'
  readonly decision: Decision
  readonly reasonCode: string
  readonly reason: string
  readonly contentReference: string
  readonly riskLevel: RiskLevel | null
  readonly promptAnalysisId: number | null
  readonly documentAnalysisId: number | null
  readonly documentId: number | null
  readonly dataCategories: readonly string[]
  readonly maskedFindings: readonly MaskedFinding[]
  readonly generationStatus: GenerationStatus
  readonly generationModel: string | null
  readonly generationError: string | null
  readonly generatedAt: string | null
  readonly createdAt: string
}

export interface AssistantAnswer {
  readonly text: string
  readonly modelName: string
  readonly generatedAt: string
}

export interface SecureQueryOutcome {
  readonly interaction: SecureInteraction
  readonly answer: AssistantAnswer | null
}

export interface InteractionPage {
  readonly items: readonly SecureInteraction[]
  readonly page: number
  readonly pageSize: number
  readonly total: number
}

export function decisionLabel(decision: Decision): string {
  return decision === 'allowed' ? 'Permitida' : 'Bloqueada'
}

export function generationStatusLabel(status: GenerationStatus): string {
  return { not_requested: 'No solicitada', skipped: 'Omitida', succeeded: 'Generada', failed: 'Fallida' }[status]
}

export function interactionContentLabel(value: SecureInteraction['contentType']): string {
  return value === 'prompt' ? 'Mensaje' : value === 'document' ? 'Documento' : 'Mensaje y documento'
}

