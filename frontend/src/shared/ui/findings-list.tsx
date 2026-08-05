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

/**
 * Masked evidence, exactly as the backend produced it.
 *
 * There is no "show original" affordance and no sanitized copy to copy or
 * download: the point of a block is that the content does not travel further.
 */
export function FindingsList({ findings, showOrigin = true }: FindingsListProps) {
  if (findings.length === 0) return null

  return (
    <ul className="findings">
      {findings.map((finding, index) => (
        <li className="finding" key={`${finding.origin}-${finding.location}-${index}`}>
          <span className="finding__type">{findingTypeLabel(finding.findingType)}</span>
          <span className="finding__severity">
            Severidad {findingSeverityLabel(finding.severity).toLowerCase()}
          </span>
          <span className="finding__detail">
            {showOrigin && <span>{findingOriginLabel(finding.origin)}</span>}
            <span>
              Evidencia enmascarada: <code className="finding__evidence">{finding.maskedEvidence}</code>
            </span>
            {finding.occurrences > 1 && <span>{finding.occurrences} coincidencias</span>}
            {finding.isPlaceholder && <span>Parece un valor de ejemplo</span>}
          </span>
        </li>
      ))}
    </ul>
  )
}
