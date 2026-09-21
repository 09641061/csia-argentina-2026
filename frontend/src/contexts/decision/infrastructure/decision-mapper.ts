import type { AssistantAnswer, GenerationStatus, MaskedFinding, RiskLevel, SecureInteraction } from '@/contexts/decision/domain/secure-interaction'
import type { AssistantAnswerResource, MaskedFindingResource, SecureInteractionResource } from '@/shared/infrastructure/api/resources'

const RISKS = new Set(['low', 'medium', 'high', 'critical'])
const GENERATION_STATUSES = new Set(['not_requested', 'skipped', 'succeeded', 'failed'])

export function toSecureInteraction(resource: SecureInteractionResource): SecureInteraction {
  return {
    id: resource.id,
    contentType: resource.content_type === 'document' ? 'document' : resource.content_type === 'prompt_with_document' ? 'prompt_with_document' : 'prompt',
    decision: resource.decision === 'allowed' ? 'allowed' : 'blocked',
    reasonCode: resource.reason_code,
    reason: resource.reason,
    contentReference: resource.content_reference,
    riskLevel: toRisk(resource.risk_level),
    promptAnalysisId: resource.prompt_analysis_id,
    documentAnalysisId: resource.document_analysis_id,
    documentId: resource.document_id,
    dataCategories: resource.data_categories,
    maskedFindings: resource.masked_findings.map(toMaskedFinding),
    generationStatus: GENERATION_STATUSES.has(resource.generation_status) ? resource.generation_status as GenerationStatus : 'not_requested',
    generationModel: resource.generation_model,
    generationError: resource.generation_error,
    generatedAt: resource.generated_at,
    createdAt: resource.created_at,
  }
}

export function toAssistantAnswer(resource: AssistantAnswerResource): AssistantAnswer {
  return { text: resource.text, modelName: resource.model_name, generatedAt: resource.generated_at }
}

function toMaskedFinding(resource: MaskedFindingResource): MaskedFinding {
  return { origin: resource.origin === 'document' ? 'document' : 'prompt', findingType: resource.finding_type, severity: toRisk(resource.severity) ?? 'medium', title: resource.title, location: resource.location, maskedEvidence: resource.masked_evidence, occurrences: resource.occurrences, isPlaceholder: resource.is_placeholder }
}

function toRisk(value: string | null): RiskLevel | null { return value && RISKS.has(value) ? value as RiskLevel : null }

