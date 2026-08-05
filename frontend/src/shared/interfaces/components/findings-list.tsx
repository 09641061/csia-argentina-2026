import { Badge } from '@/shared/interfaces/ui/badge'
import {
  findingOriginLabel,
  findingSeverityLabel,
  findingTypeLabel,
  type Finding,
} from '@/contexts/analysis-and-decision/domain/analysis/finding'

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
            <span className="text-sm font-medium text-[#e8e6df]">{findingTypeLabel(finding.findingType)}</span>
            <Badge variant="outline" className="border-white/10 text-[#aaa89f]">
              Severidad {findingSeverityLabel(finding.severity).toLowerCase()}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-[#85847d]">
            {showOrigin && <span>{findingOriginLabel(finding.origin)}</span>}
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
