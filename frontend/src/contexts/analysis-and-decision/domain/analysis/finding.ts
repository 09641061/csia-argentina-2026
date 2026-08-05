export const FINDING_SEVERITIES = ['low', 'medium', 'high', 'critical'] as const

export type FindingSeverity = (typeof FINDING_SEVERITIES)[number]

export type FindingOrigin = 'prompt' | 'document'

/**
 * A piece of sensitive material the backend found.
 *
 * `maskedEvidence` is the only representation that exists on this side: the
 * frontend never receives, reconstructs or displays the original value.
 */
export interface Finding {
  readonly origin: FindingOrigin
  readonly findingType: string
  readonly severity: FindingSeverity
  readonly title: string
  readonly location: string
  readonly maskedEvidence: string
  readonly occurrences: number
  readonly isPlaceholder: boolean
}

const FINDING_TYPE_LABELS: Record<string, string> = {
  email: 'Correo electrónico',
  full_name: 'Nombre completo',
  phone: 'Teléfono',
  personal_id: 'Documento de identidad',
  passport: 'Pasaporte',
  ip_address: 'Dirección IP',
  password: 'Contraseña',
  api_key: 'Clave de API',
  token: 'Token de autenticación',
  access_token: 'Token de acceso',
  refresh_token: 'Token de refresco',
  session_id: 'Identificador de sesión',
  session_cookie: 'Cookie de sesión',
  aws_access_key: 'Clave de acceso de AWS',
  connection_string: 'Cadena de conexión',
  credit_card: 'Tarjeta de pago',
  cvv: 'Código de seguridad de tarjeta',
  card_expiration: 'Vencimiento de tarjeta',
  bank_account: 'Cuenta bancaria',
  financial_data: 'Información financiera',
  private_key: 'Clave privada',
  debug_payload: 'Volcado de depuración',
  prompt_injection: 'Intento de manipulación',
  secret: 'Secreto',
  other: 'Otro dato sensible',
}

const SEVERITY_LABELS: Record<FindingSeverity, string> = {
  low: 'Bajo',
  medium: 'Medio',
  high: 'Alto',
  critical: 'Crítico',
}

export function findingTypeLabel(findingType: string): string {
  return FINDING_TYPE_LABELS[findingType] ?? findingType.replaceAll('_', ' ')
}

export function findingSeverityLabel(severity: FindingSeverity): string {
  return SEVERITY_LABELS[severity]
}

export function findingOriginLabel(origin: FindingOrigin): string {
  return origin === 'prompt' ? 'En la consulta' : 'En el documento'
}

/** Distinct kinds of information detected, in a stable order, for a short summary line. */
export function detectedInformationTypes(findings: readonly Finding[]): string[] {
  const seen = new Set<string>()
  const labels: string[] = []
  for (const finding of findings) {
    const label = findingTypeLabel(finding.findingType)
    if (!seen.has(label)) {
      seen.add(label)
      labels.push(label)
    }
  }
  return labels
}
