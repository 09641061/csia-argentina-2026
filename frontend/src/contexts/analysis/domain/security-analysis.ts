export type AnalysisStatus = 'running' | 'completed' | 'failed'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type FindingSeverity = RiskLevel

export interface AnalysisFinding {
  readonly origin: 'prompt' | 'document'
  readonly findingType: string
  readonly severity: FindingSeverity
  readonly title: string
  readonly description: string
  readonly location: string
  readonly maskedEvidence: string
  readonly detectionMethod: string
  readonly confidence: string
  readonly occurrences: number
  readonly dataCategory: string | null
  readonly isPlaceholder: boolean
}

export interface SecurityAnalysis {
  readonly id: number
  readonly contentType: 'prompt' | 'document'
  readonly documentId: number | null
  readonly contentReference: string
  readonly contentFingerprint: string
  readonly contentLength: number
  readonly maskedPreview: string
  readonly status: AnalysisStatus
  readonly riskLevel: RiskLevel | null
  readonly secretsRisk: RiskLevel | null
  readonly personalDataRisk: RiskLevel | null
  readonly confidence: string | null
  readonly tamperingSuspected: boolean
  readonly dataCategories: readonly string[]
  readonly estimatedSubjects: string
  readonly summary: string
  readonly rationale: string
  readonly explanation: string
  readonly modelName: string
  readonly findings: readonly AnalysisFinding[]
  readonly contentTruncated: boolean
  readonly errorMessage: string | null
  readonly analyzedAt: string | null
  readonly createdAt: string
  readonly updatedAt: string
}

export interface AnalysisPage {
  readonly items: readonly SecurityAnalysis[]
  readonly page: number
  readonly pageSize: number
  readonly total: number
}

export function analysisStatusLabel(status: AnalysisStatus): string {
  return { running: 'En proceso', completed: 'Completado', failed: 'Fallido' }[status]
}

export function contentTypeLabel(contentType: SecurityAnalysis['contentType']): string {
  return contentType === 'prompt' ? 'Mensaje' : 'Documento'
}

