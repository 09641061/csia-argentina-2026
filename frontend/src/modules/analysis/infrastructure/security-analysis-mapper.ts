import { isAnalysisStatus } from '@/modules/analysis/domain/analysis-status'
import { isRiskLevel } from '@/modules/analysis/domain/risk-level'
import type { SecurityAnalysis } from '@/modules/analysis/domain/security-analysis'
import type { SecurityAnalysisResource } from '@/shared/api/resources'

import { toFindingFromAnalysis } from './finding-mapper'

export function toSecurityAnalysis(resource: SecurityAnalysisResource): SecurityAnalysis {
  const contentType = resource.content_type === 'prompt' ? 'prompt' : 'document'
  return {
    id: resource.id,
    contentType,
    documentId: resource.document_id,
    contentReference: resource.content_reference,
    contentFingerprint: resource.content_fingerprint,
    contentLength: resource.content_length,
    maskedPreview: resource.masked_preview,
    status: isAnalysisStatus(resource.status) ? resource.status : 'failed',
    riskLevel: isRiskLevel(resource.risk_level) ? resource.risk_level : null,
    tamperingSuspected: resource.tampering_suspected,
    dataCategories: resource.data_categories,
    explanation: resource.explanation || resource.error_message || '',
    modelName: resource.model_name,
    findings: resource.findings.map((finding) => toFindingFromAnalysis(finding, contentType)),
    contentTruncated: resource.content_truncated,
    errorMessage: resource.error_message,
    analyzedAt: resource.analyzed_at,
    createdAt: resource.created_at,
  }
}
