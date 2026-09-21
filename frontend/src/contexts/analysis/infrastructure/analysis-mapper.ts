import type { AnalysisFinding, AnalysisStatus, RiskLevel, SecurityAnalysis } from '@/contexts/analysis/domain/security-analysis'
import type { AnalysisFindingResource, SecurityAnalysisResource } from '@/shared/infrastructure/api/resources'

const RISK_LEVELS = new Set(['low', 'medium', 'high', 'critical'])
const STATUSES = new Set(['running', 'completed', 'failed'])

export function toSecurityAnalysis(resource: SecurityAnalysisResource): SecurityAnalysis {
  const origin = resource.content_type === 'prompt' ? 'prompt' : 'document'
  return {
    id: resource.id,
    contentType: origin,
    documentId: resource.document_id,
    contentReference: resource.content_reference,
    contentFingerprint: resource.content_fingerprint,
    contentLength: resource.content_length,
    maskedPreview: resource.masked_preview,
    status: STATUSES.has(resource.status) ? resource.status as AnalysisStatus : 'failed',
    riskLevel: toRisk(resource.risk_level),
    secretsRisk: toRisk(resource.secrets_risk),
    personalDataRisk: toRisk(resource.personal_data_risk),
    confidence: resource.confidence,
    tamperingSuspected: resource.tampering_suspected,
    dataCategories: resource.data_categories,
    estimatedSubjects: resource.estimated_subjects,
    summary: resource.summary,
    rationale: resource.rationale,
    explanation: resource.explanation,
    modelName: resource.model_name,
    findings: resource.findings.map((finding) => toAnalysisFinding(finding, origin)),
    contentTruncated: resource.content_truncated,
    errorMessage: resource.error_message,
    analyzedAt: resource.analyzed_at,
    createdAt: resource.created_at,
    updatedAt: resource.updated_at,
  }
}

export function toAnalysisFinding(resource: AnalysisFindingResource, origin: 'prompt' | 'document'): AnalysisFinding {
  return {
    origin,
    findingType: resource.finding_type,
    severity: toRisk(resource.severity) ?? 'medium',
    title: resource.title,
    description: resource.description,
    location: resource.json_path,
    maskedEvidence: resource.evidence,
    detectionMethod: resource.detection_method,
    confidence: resource.confidence,
    occurrences: resource.occurrences,
    dataCategory: resource.data_category,
    isPlaceholder: resource.is_placeholder,
  }
}

function toRisk(value: string | null): RiskLevel | null {
  return value && RISK_LEVELS.has(value) ? value as RiskLevel : null
}

