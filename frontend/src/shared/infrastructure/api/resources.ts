/** Shape of the REST resources exactly as the backend documents them in OpenAPI. */

export interface AuthTokenResource {
  access_token: string
  token_type: 'bearer'
  expires_at: string
  username: string
}

export interface AuthenticatedUserResource {
  username: string
}

export interface MaskedFindingResource {
  origin: string
  finding_type: string
  severity: string
  title: string
  location: string
  masked_evidence: string
  occurrences: number
  is_placeholder: boolean
}

export interface AnalysisFindingResource {
  finding_id: string
  finding_type: string
  severity: string
  title: string
  description: string
  json_path: string
  evidence: string
  detection_method: string
  confidence: string
  occurrences: number
  data_category: string | null
  is_placeholder: boolean
}

export interface SecureInteractionResource {
  id: number
  content_type: string
  decision: string
  reason_code: string
  reason: string
  content_reference: string
  risk_level: string | null
  prompt_analysis_id: number | null
  document_analysis_id: number | null
  document_id: number | null
  data_categories: string[]
  masked_findings: MaskedFindingResource[]
  generation_status: string
  generation_model: string | null
  generation_error: string | null
  generated_at: string | null
  created_at: string
}

export interface AssistantAnswerResource {
  text: string
  model_name: string
  generated_at: string
}

export interface SecureQueryResponseResource {
  interaction: SecureInteractionResource
  answer: AssistantAnswerResource | null
}

export interface PageMetadataResource {
  page: number
  page_size: number
  total: number
}

export interface SecureInteractionListResource {
  items: SecureInteractionResource[]
  page: PageMetadataResource
}

export interface SecurityAnalysisResource {
  id: number
  content_type: string
  document_id: number | null
  content_reference: string
  content_fingerprint: string
  content_length: number
  masked_preview: string
  status: string
  risk_level: string | null
  secrets_risk: string | null
  personal_data_risk: string | null
  confidence: string | null
  tampering_suspected: boolean
  data_categories: string[]
  estimated_subjects: string
  summary: string
  rationale: string
  explanation: string
  model_name: string
  findings: AnalysisFindingResource[]
  content_truncated: boolean
  error_message: string | null
  analyzed_at: string | null
  created_at: string
  updated_at: string
}

export interface HealthResource {
  status: string
  database: boolean
  security_model_available: boolean
  discovery_model_available: boolean
  generation_model_available: boolean
  vision_model_available: boolean
  security_model: string
  discovery_model: string
  generation_model: string
  vision_model: string
}

export interface ChatMessageResource {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface ConversationSummaryResource {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface ConversationResource extends ConversationSummaryResource {
  messages: ChatMessageResource[]
}

export interface ChatMessageResponseResource {
  answer: string
  conversation_id: number
  model_name: string
  generated_at: string
}

export interface SecurityAnalysisListResource {
  items: SecurityAnalysisResource[]
  page: PageMetadataResource
}

export interface AnalysisFindingsResource {
  analysis_id: number
  items: AnalysisFindingResource[]
}
