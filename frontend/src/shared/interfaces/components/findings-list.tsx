import { Badge } from '@/shared/interfaces/ui/badge'

interface Finding {
  readonly origin: 'prompt' | 'document'
  readonly findingType: string
  readonly severity: 'low' | 'medium' | 'high' | 'critical'
  readonly title: string
  readonly location: string
  readonly maskedEvidence: string
  readonly occurrences: number
  readonly isPlaceholder: boolean
}

const TYPE_LABELS: Record<string, string> = {
  email: 'Correo electrónico', full_name: 'Nombre completo', phone: 'Teléfono',
  personal_id: 'Documento de identidad', passport: 'Pasaporte', ip_address: 'Dirección IP',
  password: 'Contraseña', api_key: 'Clave de API', token: 'Token de autenticación',
  access_token: 'Token de acceso', refresh_token: 'Token de refresco',
  session_id: 'Identificador de sesión', session_cookie: 'Cookie de sesión',
  aws_access_key: 'Clave de acceso de AWS', connection_string: 'Cadena de conexión',
  credit_card: 'Tarjeta de pago', cvv: 'Código de seguridad de tarjeta',
  card_expiration: 'Vencimiento de tarjeta', bank_account: 'Cuenta bancaria',
  financial_data: 'Información financiera', private_key: 'Clave privada',
  debug_payload: 'Volcado de depuración', prompt_injection: 'Intento de manipulación',
  secret: 'Secreto', other: 'Otro dato sensible',
}

const SEVERITY_LABELS = { low: 'baja', medium: 'media', high: 'alta', critical: 'crítica' } as const

interface FindingsListProps {
  readonly findings: readonly Finding[]
  readonly showOrigin?: boolean
}

/** Masked evidence exactly as the backend produced it. */
export function FindingsList({ findings, showOrigin = true }: FindingsListProps) {
  if (findings.length === 0) return null

  return (
    <ul className="divide-y divide-white/[0.07] border-y border-white/[0.07]">
      {findings.map((finding, index) => (
        <li
          className="flex flex-col gap-3 py-4"
          key={`${finding.origin}-${finding.location}-${index}`}
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-sm font-medium text-[#e8e6df]">{TYPE_LABELS[finding.findingType] ?? finding.findingType.replaceAll('_', ' ')}</span>
            <Badge variant="outline" className="border-white/10 text-[#aaa89f]">
              Severidad {SEVERITY_LABELS[finding.severity]}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-[#85847d]">
            {showOrigin && <span>{finding.origin === 'prompt' ? 'En la consulta' : 'En el documento'}</span>}
            {finding.occurrences > 1 && <span>{finding.occurrences} coincidencias</span>}
            {finding.isPlaceholder && <span>Valor de ejemplo probable</span>}
          </div>
          <p className="text-xs text-[#96958d]">
            Evidencia enmascarada:{' '}
            <code className="rounded-md bg-black/20 px-1.5 py-1 font-mono text-[#e2dfd7]">
              {finding.maskedEvidence}
            </code>
          </p>
        </li>
      ))}
    </ul>
  )
}
