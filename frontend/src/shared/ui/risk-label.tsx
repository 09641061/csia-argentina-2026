import { Badge } from '@/components/ui/badge'
import { riskLevelLabel, type RiskLevel } from '@/modules/analysis/domain/risk-level'

interface RiskLabelProps {
  readonly risk: RiskLevel | null
}

export function RiskLabel({ risk }: RiskLabelProps) {
  const variant = risk === 'low' ? 'secondary' : risk === null ? 'outline' : 'default'
  return <Badge variant={variant}>{riskLevelLabel(risk)}</Badge>
}
