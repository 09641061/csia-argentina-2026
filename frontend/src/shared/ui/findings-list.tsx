import { Badge } from '@/components/ui/badge'
import {
  findingOriginLabel,
  findingSeverityLabel,
  findingTypeLabel,
  type Finding,
} from '@/modules/analysis/domain/finding'

interface FindingsListProps {
  readonly findings: readonly Finding[]
  readonly showOrigin?: boolean
}

/** Masked evidence exactly as the backend produced it. */
export function FindingsList({ findings, showOrigin = true }: FindingsListProps) {
  if (findings.length === 0) return null

  return (
    <ul className="divide-y border-y">
      {findings.map((finding, index) => (
        <li
          className="flex flex-col gap-3 py-4"
          key={`${finding.origin}-${finding.location}-${index}`}
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-sm font-medium">{findingTypeLabel(finding.findingType)}</span>
            <Badge variant="outline">
              Severidad {findingSeverityLabel(finding.severity).toLowerCase()}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted-foreground">
            {showOrigin && <span>{findingOriginLabel(finding.origin)}</span>}
            {finding.occurrences > 1 && <span>{finding.occurrences} coincidencias</span>}
            {finding.isPlaceholder && <span>Valor de ejemplo probable</span>}
          </div>
          <p className="text-xs text-muted-foreground">
            Evidencia enmascarada:{' '}
            <code className="rounded-md bg-muted px-1.5 py-1 font-mono text-foreground">
              {finding.maskedEvidence}
            </code>
          </p>
        </li>
      ))}
    </ul>
  )
}
