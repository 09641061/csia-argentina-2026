import { riskLevelLabel, type RiskLevel } from '@/modules/analysis/domain/risk-level'

interface RiskLabelProps {
  readonly risk: RiskLevel | null
}

export function RiskLabel({ risk }: RiskLabelProps) {
  return <span className={`risk risk--${risk ?? 'unknown'}`}>{riskLevelLabel(risk)}</span>
}
