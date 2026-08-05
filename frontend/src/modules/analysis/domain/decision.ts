export const DECISIONS = ['allowed', 'blocked'] as const

export type Decision = (typeof DECISIONS)[number]

export function isDecision(value: unknown): value is Decision {
  return typeof value === 'string' && (DECISIONS as readonly string[]).includes(value)
}

export function decisionLabel(decision: Decision): string {
  return decision === 'allowed' ? 'Consulta permitida' : 'Consulta bloqueada'
}
