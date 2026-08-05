export const RISK_LEVELS = ['low', 'medium', 'high', 'critical'] as const

export type RiskLevel = (typeof RISK_LEVELS)[number]

const RISK_LABELS: Record<RiskLevel, string> = {
  low: 'Riesgo bajo',
  medium: 'Riesgo medio',
  high: 'Riesgo alto',
  critical: 'Riesgo crítico',
}

export function isRiskLevel(value: unknown): value is RiskLevel {
  return typeof value === 'string' && (RISK_LEVELS as readonly string[]).includes(value)
}

/**
 * Human label for a risk level.
 *
 * `null` is not "low": it means the review never produced a verdict, and saying
 * "bajo" there would be exactly the reassurance the product must never give.
 */
export function riskLevelLabel(risk: RiskLevel | null): string {
  return risk === null ? 'Riesgo no verificado' : RISK_LABELS[risk]
}
