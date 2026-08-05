export const ANALYSIS_STATUSES = ['running', 'completed', 'failed'] as const

export type AnalysisStatus = (typeof ANALYSIS_STATUSES)[number]

const ANALYSIS_STATUS_LABELS: Record<AnalysisStatus, string> = {
  running: 'Revisión en curso',
  completed: 'Revisión completada',
  failed: 'Revisión fallida',
}

export function isAnalysisStatus(value: unknown): value is AnalysisStatus {
  return typeof value === 'string' && (ANALYSIS_STATUSES as readonly string[]).includes(value)
}

export function analysisStatusLabel(status: AnalysisStatus): string {
  return ANALYSIS_STATUS_LABELS[status]
}
