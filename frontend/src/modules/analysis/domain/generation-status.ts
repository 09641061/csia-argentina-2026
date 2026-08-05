export const GENERATION_STATUSES = ['not_requested', 'skipped', 'succeeded', 'failed'] as const

export type GenerationStatus = (typeof GENERATION_STATUSES)[number]

const GENERATION_STATUS_LABELS: Record<GenerationStatus, string> = {
  not_requested: 'Sin respuesta solicitada',
  skipped: 'No se envió al asistente',
  succeeded: 'Respuesta generada',
  failed: 'No se pudo generar la respuesta',
}

export function isGenerationStatus(value: unknown): value is GenerationStatus {
  return typeof value === 'string' && (GENERATION_STATUSES as readonly string[]).includes(value)
}

export function generationStatusLabel(status: GenerationStatus): string {
  return GENERATION_STATUS_LABELS[status]
}
