import { isContentType, type ContentType } from '@/modules/analysis/domain/content-type'
import { isDecision } from '@/modules/analysis/domain/decision'
import {
  isGenerationStatus,
  type GenerationStatus,
} from '@/modules/analysis/domain/generation-status'
import { isRiskLevel } from '@/modules/analysis/domain/risk-level'
import { toFinding } from '@/modules/analysis/infrastructure/finding-mapper'
import type { AssistantResponse } from '@/modules/secure-query/domain/assistant-response'
import type { SecureInteraction } from '@/modules/secure-query/domain/secure-interaction'
import type {
  AssistantAnswerResource,
  SecureInteractionResource,
} from '@/shared/api/resources'

export function toSecureInteraction(resource: SecureInteractionResource): SecureInteraction {
  return {
    id: resource.id,
    contentType: toContentType(resource.content_type),
    // An unrecognized verdict is treated as blocked: the safe reading is always
    // "we could not confirm this was allowed".
    decision: isDecision(resource.decision) ? resource.decision : 'blocked',
    reasonCode: resource.reason_code,
    reason: resource.reason,
    contentReference: resource.content_reference,
    riskLevel: isRiskLevel(resource.risk_level) ? resource.risk_level : null,
    promptAnalysisId: resource.prompt_analysis_id,
    documentAnalysisId: resource.document_analysis_id,
    documentId: resource.document_id,
    dataCategories: resource.data_categories,
    maskedFindings: resource.masked_findings.map(toFinding),
    generationStatus: toGenerationStatus(resource.generation_status),
    generationModel: resource.generation_model,
    generationError: resource.generation_error,
    generatedAt: resource.generated_at,
    createdAt: resource.created_at,
  }
}

export function toAssistantResponse(resource: AssistantAnswerResource): AssistantResponse {
  return {
    text: resource.text,
    modelName: resource.model_name,
    generatedAt: resource.generated_at,
  }
}

function toContentType(value: string): ContentType {
  return isContentType(value) ? value : 'prompt'
}

function toGenerationStatus(value: string): GenerationStatus {
  return isGenerationStatus(value) ? value : 'not_requested'
}
