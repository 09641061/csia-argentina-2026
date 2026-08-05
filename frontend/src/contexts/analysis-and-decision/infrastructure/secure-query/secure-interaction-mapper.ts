import { isContentType, type ContentType } from '@/contexts/analysis-and-decision/domain/analysis/content-type'
import { isDecision } from '@/contexts/analysis-and-decision/domain/analysis/decision'
import {
  isGenerationStatus,
  type GenerationStatus,
} from '@/contexts/analysis-and-decision/domain/analysis/generation-status'
import { isRiskLevel } from '@/contexts/analysis-and-decision/domain/analysis/risk-level'
import { toFinding } from '@/contexts/analysis-and-decision/infrastructure/analysis/finding-mapper'
import type { AssistantResponse } from '@/contexts/analysis-and-decision/domain/secure-query/assistant-response'
import type { SecureInteraction } from '@/contexts/analysis-and-decision/domain/secure-query/secure-interaction'
import type {
  AssistantAnswerResource,
  SecureInteractionResource,
} from '@/shared/infrastructure/api/resources'

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
