import type {
  SecureInteractionResource,
  SecureQueryResponseResource,
  SecurityAnalysisResource,
} from '@/shared/api/resources'

export function allowedInteractionResource(
  overrides: Partial<SecureInteractionResource> = {},
): SecureInteractionResource {
  return {
    id: 1,
    content_type: 'prompt',
    decision: 'allowed',
    reason_code: 'content_is_safe',
    reason: 'No se detectó información sensible en el contenido revisado.',
    content_reference: 'Consulta escrita',
    risk_level: 'low',
    prompt_analysis_id: 10,
    document_analysis_id: null,
    document_id: null,
    data_categories: [],
    masked_findings: [],
    generation_status: 'succeeded',
    generation_model: 'llama3.2:3b',
    generation_error: null,
    generated_at: '2026-08-04T12:00:00Z',
    created_at: '2026-08-04T12:00:00Z',
    ...overrides,
  }
}

export function blockedInteractionResource(
  overrides: Partial<SecureInteractionResource> = {},
): SecureInteractionResource {
  return allowedInteractionResource({
    id: 2,
    decision: 'blocked',
    reason_code: 'prompt_contains_sensitive_data',
    reason: 'La consulta contiene información sensible.',
    risk_level: 'high',
    data_categories: ['password'],
    masked_findings: [
      {
        origin: 'prompt',
        finding_type: 'password',
        severity: 'high',
        title: 'Contraseña en la consulta',
        location: '$.prompt',
        masked_evidence: 'Sup*********23',
        occurrences: 1,
        is_placeholder: false,
      },
    ],
    generation_status: 'skipped',
    generation_model: null,
    generated_at: null,
    ...overrides,
  })
}

export function secureQueryResponse(
  interaction: SecureInteractionResource,
  answerText: string | null = 'Una respuesta del asistente local.',
): SecureQueryResponseResource {
  return {
    interaction,
    answer: answerText
      ? { text: answerText, model_name: 'llama3.2:3b', generated_at: '2026-08-04T12:00:05Z' }
      : null,
  }
}

export function analysisResource(
  overrides: Partial<SecurityAnalysisResource> = {},
): SecurityAnalysisResource {
  return {
    id: 10,
    content_type: 'prompt',
    document_id: null,
    content_reference: 'Consulta escrita',
    content_fingerprint: 'a'.repeat(64),
    content_length: 42,
    masked_preview: 'Explícame las ventajas de una arquitectura orientada a eventos.',
    status: 'completed',
    risk_level: 'low',
    secrets_risk: 'none',
    personal_data_risk: 'low',
    confidence: 'high',
    tampering_suspected: false,
    data_categories: [],
    estimated_subjects: '0',
    summary: 'Consulta técnica general.',
    rationale: 'No se encontraron hallazgos deterministas.',
    explanation: 'Consulta técnica general. No se encontraron hallazgos deterministas.',
    model_name: 'llama3.2:3b',
    findings: [],
    content_truncated: false,
    error_message: null,
    analyzed_at: '2026-08-04T12:00:00Z',
    created_at: '2026-08-04T12:00:00Z',
    updated_at: '2026-08-04T12:00:00Z',
    ...overrides,
  }
}

/** Minimal fetch stub that answers by URL, so tests never touch the network. */
export function stubFetch(routes: Record<string, unknown>, status = 200) {
  return vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.toString()
    const matched = Object.entries(routes).find(([pattern]) => url.includes(pattern))
    if (!matched) {
      return new Response(JSON.stringify({ detail: 'No encontramos lo que buscabas.' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    return new Response(JSON.stringify(matched[1]), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
}
