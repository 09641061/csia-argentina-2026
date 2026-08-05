import type { AnalysisStatus } from './analysis-status'
import type { Finding } from './finding'
import type { RiskLevel } from './risk-level'

/**
 * One security review, as the history detail shows it.
 *
 * There is no reviewed content here: the backend keeps a fingerprint and a
 * masked preview, and that is all this type is allowed to carry.
 */
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
  readonly tamperingSuspected: boolean
  readonly dataCategories: readonly string[]
  readonly explanation: string
  readonly modelName: string
  readonly findings: readonly Finding[]
  readonly contentTruncated: boolean
  readonly errorMessage: string | null
  readonly analyzedAt: string | null
  readonly createdAt: string
}
